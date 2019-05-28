from app import db


class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String())
    phone = db.Column(db.String())
    customer_code = db.Column(db.String())
    create_date = db.Column(db.String())

    def __init__(self, user_id, phone, customer_code, create_date):
        self.user_id = user_id
        self.phone = phone
        self.customer_code = customer_code
        self.create_date = create_date


    def __repr__(self):
        return '<id {}>'.format(self.id)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone': self.phone,
            'customer_code': self.customer_code,
            'create_date': self.create_date
        }
