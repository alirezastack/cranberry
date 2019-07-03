from cranberry.core.models.refresh_token import RefreshTokenSchema
from bson import ObjectId


class RefreshTokenStore:
    def __init__(self, db, app):
        self.app = app
        self.db = db
        self.refresh_token_schema = RefreshTokenSchema()

    def save(self, data):
        # raise validation error on invalid data
        self.refresh_token_schema.load(data)
        clean_data = self.refresh_token_schema.dump(data)
        return self.db.save(clean_data)

    def get_cart_by_id(self, cart_id):
        cart = self.db.find_one({'_id': ObjectId(cart_id)}, {'created_at': 0})
        clean_data = self.refresh_token_schema.load(cart)
        return clean_data
