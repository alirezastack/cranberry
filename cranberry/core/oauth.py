import datetime

from olive.consts import UTC_DATE_FORMAT
from olive.proto import zoodroom_pb2_grpc, zoodroom_pb2
from olive.authentication import Authentication
from olive.exc import ClientNotFound, AccessTokenNotFound
from marshmallow import ValidationError
import traceback
import ujson
from olive.validation import Validation


class CranberryService(zoodroom_pb2_grpc.CranberryServiceServicer):
    def __init__(self, access_token_store, refresh_token_store, client_store, app):
        self.access_token_store = access_token_store
        self.refresh_token_store = refresh_token_store
        self.client_store = client_store
        self.app = app
        self.expires_in = app.config['cranberry']['oauth']['expires_in']

    def ResourceOwnerPasswordCredential(self, request, context):
        try:
            self.app.log.debug('validating client {}'.format(request.client_id))
            self.client_store.exists(client_id=request.client_id,
                                     client_secret=request.client_secret)

            self.app.log.debug('authenticating user {} with password: ****'.format(request.username))
            # TODO authenticate user in the future -> user.authenticate_user & user.get_user_by_username
            # TODO suppose it is Authenticated by now and fetch user data
            user_id = 'A-SAMPLE-USER-ID'
            auth = Authentication()
            access_token_payload = {
                'client_id': request.client_id,
                'access_token': auth.generate_token(user_id),
                'refresh_token': auth.generate_token(user_id),
                'expires_in': self.expires_in,
                'user_id': user_id,
                'scope': request.scope.split(','),
                'grant_type': 'password'
            }

            access_token_id = self.access_token_store.save(access_token_payload)
            self.app.log.debug('access-token has been saved successfully: {}'.format(access_token_id))

            # Set a cached value
            self.app.log.debug('cache data in redis')
            self.app.cache.set('my_key', 'my value')

            # TODO save refresh token too

            # res = self.access_token_store.get_access_token_by_id(token_id=str(access_token_id))
            # self.app.log.debug(res)

            return zoodroom_pb2.ResourceOwnerPasswordCredentialResponse(
                access_token=access_token_payload['access_token'],
                refresh_token=access_token_payload['refresh_token'],
                expires_in=self.expires_in,
                scope=request.scope
            )
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return zoodroom_pb2.ResourceOwnerPasswordCredentialResponse(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': ujson.dumps([])
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return zoodroom_pb2.ResourceOwnerPasswordCredentialResponse(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': ujson.dumps([12, 13, 14])
                }
            )
        except ClientNotFound as cnf:
            self.app.log.error('Client Not Found: {}'.format(traceback.format_exc()))
            return zoodroom_pb2.ResourceOwnerPasswordCredentialResponse(
                error={
                    'code': 'client_not_found',
                    'message': 'Client Not found!',
                    'details': ujson.dumps([])
                }
            )
        except Exception as e:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return zoodroom_pb2.ResourceOwnerPasswordCredentialResponse(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': ujson.dumps([])
                }
            )

    def CreateClient(self, request, context):
        try:
            self.app.log.debug('checking whether client {} exists...'.format(request.client_id))
            try:
                self.client_store.is_client_id_exists(client_id=request.client_id)
                return zoodroom_pb2.CreateClientResponse(
                    error={
                        'code': 'client_exists',
                        'message': 'Client {} is duplicate'.format(request.client_id),
                        'details': ujson.dumps([request.client_id])
                    }
                )
            except ClientNotFound:
                self.app.log.info('client id {} is free for registration'.format(request.client_id))

            self.app.log.debug('verifying URL schemes')
            for url in request.redirection_uris:
                if not Validation.is_url_valid(url):
                    return zoodroom_pb2.CreateClientResponse(
                        error={
                            'code': 'invalid_redirection_uri',
                            'message': 'Redirection URI {} is not valid!'.format(url),
                            'details': ujson.dumps([url])
                        }
                    )

            out = self.client_store.save({
                'client_id': request.client_id,
                'client_secret': request.client_secret,
                'redirection_uris': request.redirection_uris,
                'fullname': request.fullname,
                'logo': request.logo,
                'description': request.description,
            })
            self.app.log.info('client creation output: {}'.format(out))

            return zoodroom_pb2.CreateClientResponse(
                created=True
            )
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return zoodroom_pb2.CreateClientResponse(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': ujson.dumps([])
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return zoodroom_pb2.CreateClientResponse(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': ujson.dumps([12, 13, 14])
                }
            )
        except Exception as e:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return zoodroom_pb2.CreateClientResponse(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': ujson.dumps([])
                }
            )

    def VerifyAccessToken(self, request, context):
        try:
            self.app.log.debug('getting token {} for client {}...'.format(request.access_token, request.client_id))
            token = self.access_token_store.get_one(client_id=request.client_id,
                                                    access_token=request.access_token)
            self.app.log.debug('token information: {}'.format(token))

            issue_date_obj = datetime.datetime.strptime(token['created_at'], UTC_DATE_FORMAT)
            expires_in_second_obj = datetime.timedelta(seconds=token['expires_in'])
            expires_in_obj = issue_date_obj + expires_in_second_obj
            if expires_in_obj < datetime.datetime.utcnow():
                hours, remainder = divmod((datetime.datetime.utcnow() - expires_in_obj).seconds, 3600)
                self.app.log.error('access token {} is expired on {} for {} days, {} hour(s), {} minute(s)'.format(
                    request.access_token,
                    expires_in_obj.strftime(UTC_DATE_FORMAT),
                    (datetime.datetime.utcnow() - expires_in_obj).days,
                    hours,
                    remainder//60))
                return zoodroom_pb2.VerifyAccessTokenResponse(
                    error={
                        'code': 'invalid_token',
                        'message': 'The access token provided is expired, revoked or malformed.'
                    }
                )

            return zoodroom_pb2.VerifyAccessTokenResponse()
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return zoodroom_pb2.VerifyAccessTokenResponse(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': ujson.dumps([])
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return zoodroom_pb2.VerifyAccessTokenResponse(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': ujson.dumps([12, 13, 14])
                }
            )
        except AccessTokenNotFound as atnf:
            self.app.log.error('token not found error:\r\n{}'.format(traceback.format_exc()))
            return zoodroom_pb2.VerifyAccessTokenResponse(
                error={
                    'code': 'invalid_token',
                    'message': 'The access token provided is expired, revoked or malformed.',
                    'details': ujson.dumps([])
                }
            )
        except Exception as e:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return zoodroom_pb2.VerifyAccessTokenResponse(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': ujson.dumps([])
                }
            )
