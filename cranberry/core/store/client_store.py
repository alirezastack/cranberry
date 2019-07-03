from cranberry.core.models.client import ClientSchema
from olive.exc import ClientNotFound, DuplicateClient
from bson import ObjectId


class ClientStore:
    def __init__(self, db, app):
        self.app = app
        self.db = db
        self.client_schema = ClientSchema()

    def save(self, data):
        # raise validation error on invalid data
        self.client_schema.load(data)
        clean_data = self.client_schema.dump(data)

        if self.db.count({'client_id': data['client_id']}) >= 1:
            raise DuplicateClient

        return self.db.save(clean_data)

    def get_client_by_id(self, client_id):
        client = self.db.find_one({'_id': ObjectId(client_id)}, {'created_at': 0})
        clean_data = self.client_schema.load(client)
        return clean_data

    def get_client_by_client_id(self, client_id):
        client = self.db.find_one({'client_id': client_id}, {'created_at': 0})
        if not client:
            raise ClientNotFound

        clean_data = self.client_schema.load(client)
        return clean_data

    def exists(self, client_id, client_secret):
        self.app.log.debug('checking if client: {} exists with client secret: ****'.format(client_id))
        if self.db.count({'client_id': client_id, 'client_secret': client_secret}) == 0:
            raise ClientNotFound

        self.app.log.info('client {} exists'.format(client_id))
        return True

    def is_client_id_exists(self, client_id):
        self.app.log.debug('checking if client: {} exists...'.format(client_id))
        if self.db.count({'client_id': client_id}) == 0:
            raise ClientNotFound

        self.app.log.info('client {} exists'.format(client_id))
        return True
