from cranberry.core.store.refresh_token_store import RefreshTokenStore
from cranberry.core.store.access_token_store import AccessTokenStore
from olive.proto import zoodroom_pb2_grpc, health_pb2_grpc
from cranberry.core.store.client_store import ClientStore
from olive.store.mongo_connection import MongoConnection
from cranberry.core.oauth import CranberryService
from olive.proto.health import HealthService
from cranberry.controllers.base import Base
from olive.exc import CranberryServiceError
from olive.proto.rpc import GRPCServerBase
from cement.core.exc import CaughtSignal
from cement import App, TestApp


class CranberryApp(App):
    """Cranberry primary application."""

    class Meta:
        label = 'cranberry'

        # configuration defaults
        # config_defaults = CONFIG

        # call sys.exit() on close
        close_on_exit = True

        # load additional framework extensions
        extensions = [
            'yaml',
            'colorlog',
            'redis',
        ]

        # configuration handler
        config_handler = 'yaml'

        cache_handler = 'redis'

        # configuration file suffix
        config_file_suffix = '.yml'

        # set the log handler
        log_handler = 'colorlog'

        # register handlers
        handlers = [
            Base
        ]

    def run(self):
        expires_in = int(self.config['cranberry']['oauth']['expires_in'])
        mongodb_cfg = self.config['cranberry']['mongodb']
        self.log.debug('initiating MongoDB configuration...')
        mongo = MongoConnection(mongodb_cfg, self)
        self.log.info('current database: {}'.format(mongo))
        target_database = mongo.service_db
        access_token_store = AccessTokenStore(target_database.access_token, self)
        refresh_token_store = RefreshTokenStore(target_database.refresh_token, self)
        client_store = ClientStore(target_database.oauth_client, self)
        self.log.info('current service name: ' + self._meta.label)

        # Passing self for app is suggested by Cement Core Developer:
        #   - https://github.com/datafolklabs/cement/issues/566
        cs = CranberryServer(service_name=self._meta.label,
                             access_token_store=access_token_store,
                             refresh_token_store=refresh_token_store,
                             client_store=client_store,
                             expires_in=expires_in,
                             app=self)
        cs.start()


class CranberryServer(GRPCServerBase):
    def __init__(self, service_name, access_token_store, refresh_token_store, client_store, expires_in, app):
        super(CranberryServer, self).__init__(service=service_name, app=app)

        # add class to gRPC server
        service = CranberryService(access_token_store=access_token_store,
                                   refresh_token_store=refresh_token_store,
                                   client_store=client_store,
                                   expires_in=expires_in,
                                   app=app)
        health_service = HealthService(app=app)

        # adds a CranberryService to a gRPC.Server
        zoodroom_pb2_grpc.add_CranberryServiceServicer_to_server(service, self.server)
        health_pb2_grpc.add_HealthServicer_to_server(health_service, self.server)


class CranberryAppTest(TestApp, CranberryApp):
    """A sub-class of CranberryService that is better suited for testing."""

    class Meta:
        label = 'cranberry'


def main():
    with CranberryApp() as app:
        try:
            app.run()
        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CranberryServiceError as e:
            print('CranberryError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
