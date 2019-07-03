from cranberry.core.models.access_token import AccessTokenSchema
from olive.exc import AccessTokenNotFound
from bson import ObjectId


class AccessTokenStore:
    def __init__(self, db, app):
        self.app = app
        self.db = db
        self.access_token_schema = AccessTokenSchema()

    def save(self, data):
        # raise validation error on invalid data
        self.access_token_schema.load(data)
        clean_data = self.access_token_schema.dump(data)
        return self.db.save(clean_data)

    def get_access_token_by_id(self, token_id):
        access_token = self.db.find_one({'_id': ObjectId(token_id)}, {'created_at': 0})
        clean_data = self.access_token_schema.load(access_token)
        return clean_data

    def get_one(self, client_id, access_token):
        token = self.db.find_one({'client_id': client_id, 'access_token': access_token})
        if not token:
            raise AccessTokenNotFound

        self.access_token_schema.load(token)
        return token
