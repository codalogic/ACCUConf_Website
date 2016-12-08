from accuconf import db

from accuconf.proposals.utils.roles import Role


class User(db.Model):
    user_id = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(512), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(18), nullable=False)
    bio = db.Column(db.Text(), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    country = db.Column(db.String(5), nullable=False)
    state = db.Column(db.String(10), nullable=False)
    postal_code = db.Column(db.String(40), nullable=False)
    town_city = db.Column(db.String(30), nullable=False)
    street_address = db.Column(db.String(128), nullable=False)
    proposals = db.relationship('Proposal', uselist=True, backref=db.backref('proposed_by'), foreign_keys="Proposal.proposer")

    def __init__(self, user_id, password, first_name, last_name, phone, bio, country, state, postal_code, town_city, street_address):
        local_variables = locals()
        for item in ('user_id', 'password', 'first_name', 'last_name', 'phone', 'bio', 'country', 'state', 'postal_code', 'town_city', 'street_address'):
            value = local_variables[item]
            if not isinstance(value, str):
                raise TypeError('{} must be a string value.'.format(item))
            if value == '':
                raise ValueError('{} cannot be an empty string.'.format(item))
        self.user_id = user_id
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.bio = bio
        self.role = Role.user
        self.country = country
        self.state = state
        self.postal_code = postal_code
        self.town_city = town_city
        self.street_address = street_address
