from accuconf import db
from accuconf.proposals.utils.proposals import SessionType, SessionCategory, ProposalState


class Proposal(db.Model):
    __tablename__ = "proposals"
    id = db.Column(db.Integer, primary_key=True)
    proposer = db.Column(db.String(100), db.ForeignKey('users.user_id'))
    title = db.Column(db.String(150), nullable=False)
    session_type = db.Column(db.Enum(SessionType), nullable=False)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(SessionCategory), nullable=False)
    status = db.Column(db.Enum(ProposalState), nullable=False)
    presenters = db.relationship('ProposalPresenter', uselist=True)
    reviews = db.relationship('ProposalReview', uselist=True)
    comments = db.relationship('ProposalComment', uselist=True)
    session_proposer = db.relationship('User', foreign_keys='Proposal.proposer')

    def __init__(self, proposer, title, session_type, text):
        if isinstance(proposer, str):
            self.proposer = proposer
        else:
            raise TypeError('proposer must be a string value.')
        if isinstance(title, str):
            self.title = title
        else:
            raise TypeError('title must be a string value.')
        if isinstance(session_type, SessionType):
            self.session_type = session_type
        else:
            raise TypeError('session_type should be a SessionType value.')
        if isinstance(text, str):
            self.text = text
        else:
            raise TypeError('text must be a string value.')
        self.status = ProposalState.submitted
        self.category = SessionCategory.not_sure


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
