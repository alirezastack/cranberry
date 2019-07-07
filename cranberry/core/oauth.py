from olive.proto.zoodroom_pb2 import ResourceOwnerPasswordCredentialResponse, ResourceOwnerPasswordCredentialRequest, \
    CreateClientRequest, CreateClientResponse, VerifyAccessTokenRequest, VerifyAccessTokenResponse, \
    GetClientByClientIdRequest, GetClientByClientIdResponse, RefreshTokenRequest, RefreshTokenResponse
from olive.exc import ClientNotFound, AccessTokenNotFound
from olive.authentication import Authentication
from olive.proto import zoodroom_pb2_grpc
from olive.consts import UTC_DATE_FORMAT
from marshmallow import ValidationError
from olive.validation import Validation
from olive.proto.rpc import Response
import traceback
import datetime


class CranberryService(zoodroom_pb2_grpc.CranberryServiceServicer):
    def __init__(self, access_token_store, refresh_token_store, client_store, app):
        self.access_token_store = access_token_store
        self.refresh_token_store = refresh_token_store
        self.client_store = client_store
        self.app = app
        self.expires_in = app.config['cranberry']['oauth']['expires_in']

    def ResourceOwnerPasswordCredential(self, request: ResourceOwnerPasswordCredentialRequest, context) \
            -> ResourceOwnerPasswordCredentialResponse:
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
                'scope': list(request.scope),
                'grant_type': 'password'
            }

            self.app.log.debug('saving access token:\n{}'.format(access_token_payload))
            access_token_id = self.access_token_store.save(access_token_payload)
            self.app.log.debug('access-token has been saved successfully: {}'.format(access_token_id))

            refresh_token_payload = {
                'client_id': request.client_id,
                'refresh_token': access_token_payload['refresh_token'],
                'expires_in': self.expires_in,
                'user_id': user_id,
                'scope': list(request.scope),
                'grant_type': 'password'
            }

            self.app.log.debug('saving refresh token:\n{}'.format(refresh_token_payload))
            refresh_token_id = self.refresh_token_store.save(refresh_token_payload)
            self.app.log.debug('refresh token has been saved successfully: {}'.format(refresh_token_id))

            return Response.message(
                access_token=access_token_payload['access_token'],
                refresh_token=access_token_payload['refresh_token'],
                expires_in=self.expires_in,
                scope=request.scope
            )
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': []
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return Response.message(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': []
                }
            )
        except ClientNotFound:
            self.app.log.error('Client Not Found: {}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'client_not_found',
                    'message': 'Client Not found!',
                    'details': []
                }
            )
        except Exception:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': []
                }
            )

    def CreateClient(self, request: CreateClientRequest, context) -> CreateClientResponse:
        try:
            try:
                self.client_store.is_client_id_exists(client_id=request.client_id)
                return Response.message(
                    error={
                        'code': 'client_exists',
                        'message': 'Client {} is duplicate'.format(request.client_id),
                        'details': [request.client_id]
                    })
            except ClientNotFound:
                self.app.log.info('client id {} is free for registration'.format(request.client_id))

            self.app.log.debug('verifying URL schemes')
            for url in request.redirection_uris:
                if not Validation.is_url_valid(url):
                    return Response.message(
                        error={
                            'code': 'invalid_redirection_uri',
                            'message': 'Redirection URI {} is not valid!'.format(url),
                            'details': [url]
                        }
                    )

            out = self.client_store.save({
                'client_id': request.client_id,
                'client_secret': request.client_secret,
                'redirection_uris': request.redirection_uris,
                'fullname': request.fullname,
                'logo': request.logo,
                'description': request.description,
                'is_active': request.is_active or False,
            })
            self.app.log.info('client creation output: {}'.format(out))

            return Response.message(
                created=True
            )
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': []
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return Response.message(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': []
                }
            )
        except Exception:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': []
                }
            )

    def VerifyAccessToken(self, request: VerifyAccessTokenRequest, context) -> VerifyAccessTokenResponse:
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
                    remainder // 60))
                return Response.message(
                    error={
                        'code': 'invalid_token',
                        'message': 'The access token provided is expired, revoked or malformed.'
                    }
                )

            return Response.message()
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': []
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return Response.message(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': []
                }
            )
        except AccessTokenNotFound:
            self.app.log.error('token not found error:\r\n{}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'invalid_token',
                    'message': 'The access token provided is expired, revoked or malformed.',
                    'details': []
                }
            )
        except Exception:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': []
                }
            )

    def GetClientByClientId(self, request: GetClientByClientIdRequest, context) -> GetClientByClientIdResponse:
        try:
            self.app.log.debug('getting client {}'.format(request.client_id))
            client = self.client_store.get_client_by_client_id(client_id=request.client_id)
            self.app.log.debug('client information: {}'.format(client))
            return Response.message(
                client_id=request.client_id,
                client_secret=client['client_secret'],
                redirection_uris=client['redirection_uris'],
                fullname=client['fullname'],
                logo=client['logo'],
                description=client['description']
            )
        except ClientNotFound:
            self.app.log.error('Client Not Found: {}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'client_not_found',
                    'message': 'Client Not found!',
                    'details': []
                }
            )
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': []
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return Response.message(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': []
                }
            )
        except Exception:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': []
                }
            )

    def RefreshToken(self, request: RefreshTokenRequest, context) -> RefreshTokenResponse:
        try:
            raise NotImplemented
        except ValueError as ve:
            self.app.log.error('Schema value error:\r\n{}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'value_error',
                    'message': str(ve),
                    'details': []
                }
            )
        except ValidationError as ve:
            self.app.log.error('Schema validation error:\r\n{}'.format(ve.messages))
            return Response.message(
                error={
                    'code': 'invalid_schema',
                    'message': 'Given data is not valid!',
                    'details': []
                }
            )
        except Exception:
            self.app.log.error('An error occurred: {}'.format(traceback.format_exc()))
            return Response.message(
                error={
                    'code': 'server_error',
                    'message': 'Server is in maintenance mode',
                    'details': []
                }
            )
