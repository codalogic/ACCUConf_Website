from accuconf import db

from accuconf.proposals.utils.roles import Role


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(512), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(18), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    country = db.Column(db.String(5), nullable=False)
    state = db.Column(db.String(10), nullable=False)
    postal_code = db.Column(db.String(40), nullable=False)
    town_city = db.Column(db.String(30), nullable=False)
    street_address = db.Column(db.String(128), nullable=False)
    proposals = db.relationship('Proposal', back_populates='proposer')
    scores = db.relationship('Score', backref='scorer')
    comments = db.relationship('Comment', backref='commenter')

    def __init__(self, email, password, first_name, last_name, phone, country, state, postal_code, town_city, street_address):
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.role = Role.user
        self.country = country
        self.state = state
        self.postal_code = postal_code
        self.town_city = town_city
        self.street_address = street_address
