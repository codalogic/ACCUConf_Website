from accuconf import db
from accuconf.proposals.utils.proposals import *


class Proposal(db.Model):
    __tablename__ = "proposals"
    id = db.Column(db.Integer, primary_key=True)
    proposer = db.Column(db.String(100), db.ForeignKey('users.user_id'))
    title = db.Column(db.String(150), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)
    text = db.Column(db.Text, nullable=False)
    presenters = db.relationship('ProposalPresenter', uselist=True)
    status = db.relationship('ProposalStatus', uselist=False)
    reviews = db.relationship('ProposalReview', uselist=True)
    comments = db.relationship('ProposalComment', uselist=True)
    categories = db.relationship('ProposalCategory', uselist=True)
    session_proposer = db.relationship('User', foreign_keys='Proposal.proposer')

    def __init__(self, proposer, title, session_type, text):
        self.proposer = proposer
        self.title = title
        if issubclass(type(session_type), ProposalType):
            self.session_type = session_type.proposalType()
        else:
            raise TypeError("session_type should be of type accuconf.proposals.ProposalType")
        self.text = text


class ProposalPresenter(db.Model):
    __tablename__ = "proposal_presenters"
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'))
    is_lead = db.Column(db.Boolean, nullable=False)
    email = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)

    def __init__(self, proposal_id, email, lead, fname, lname, country, state):
        self.proposal_id = proposal_id
        self.email = email
        self.is_lead = lead
        self.first_name = fname
        self.last_name = lname
        self.country = country
        self.state = state


class ProposalStatus(db.Model):
    __tablename__ = "proposal_states"
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'))
    state = db.Column(db.String(20), nullable=False)

    def __init__(self, proposal_id, state):
        self.proposal_id = proposal_id
        if issubclass(type(state), ProposalState):
            self.state = state.state()
        else:
            raise TypeError("state should be of type accuconf.proposals.ProposalState")


class ProposalReview(db.Model):
    __tablename__ = "proposal_reviews"
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'))
    reviewer = db.Column(db.String(100), db.ForeignKey('users.user_id'))
    score = db.Column(db.Integer)

    def __init__(self, proposal_id, reviewer, score):
        self.proposal_id = proposal_id
        self.reviewer = reviewer
        self.score = score


class ProposalComment(db.Model):
    __tablename__ = "proposal_comments"
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'))
    commenter = db.Column(db.String(100), db.ForeignKey('users.user_id'))
    comment = db.Column(db.Text)

    def __init__(self, proposal_id, commenter, comment):
        self.proposal_id = proposal_id
        self.commenter = commenter
        self.comment = comment


class ProposalCategory(db.Model):
    __tablename__ = "proposal_categories"
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'))
    category = db.Column(db.String(100), nullable=False)

    def __init__(self, proposal_id, category):
        self.proposal_id = proposal_id
        if type(category) == ProposalCategory:
            self.category = category
        else:
            raise TypeError("category should be of type accuconf.proposals.ProposalCategory")
