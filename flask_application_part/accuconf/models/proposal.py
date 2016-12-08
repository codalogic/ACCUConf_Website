from accuconf import db
from accuconf.proposals.utils.proposals import SessionType, SessionCategory, ProposalState


class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposer = db.Column(db.String(100), db.ForeignKey('user.user_id'))
    title = db.Column(db.String(150), nullable=False)
    session_type = db.Column(db.Enum(SessionType), nullable=False)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(SessionCategory), nullable=False)
    status = db.Column(db.Enum(ProposalState), nullable=False)
    presenters = db.relationship('ProposalPresenter', uselist=True)
    reviews = db.relationship('ProposalReview', uselist=True)
    comments = db.relationship('ProposalComment', uselist=True)

    def __init__(self, proposer, title, session_type, text, category=SessionCategory.not_sure, status=ProposalState.submitted):
        if isinstance(proposer, str):
            if proposer == '':
                raise ValueError('proposer cannot be an empty string.')
            self.proposer = proposer
        else:
            raise TypeError('proposer must be a string value.')
        if isinstance(title, str):
            if title == '':
                raise ValueError('title cannot be an empty string.')
            self.title = title
        else:
            raise TypeError('title must be a string value.')
        if isinstance(session_type, SessionType):
            self.session_type = session_type
        else:
            raise TypeError('session_type must be a SessionType value.')
        if isinstance(text, str):
            if text == '':
                raise ValueError('text cannot be an empty string.')
            self.text = text
        else:
            raise TypeError('text must be a string value.')
        if isinstance(category, SessionCategory):
            self.category = SessionCategory.not_sure
        else:
            raise TypeError('category must be a SessionCategory value.')
        if isinstance(status, ProposalState):
            self.status = ProposalState.submitted
        else:
            raise TypeError('status must be a ProposalState value.')


class ProposalPresenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
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
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    reviewer = db.Column(db.String(100), db.ForeignKey('user.user_id'))
    score = db.Column(db.Integer)

    def __init__(self, proposal_id, reviewer, score):
        self.proposal_id = proposal_id
        self.reviewer = reviewer
        self.score = score


class ProposalComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    commenter = db.Column(db.String(100), db.ForeignKey('user.user_id'))
    comment = db.Column(db.Text)

    def __init__(self, proposal_id, commenter, comment):
        self.proposal_id = proposal_id
        self.commenter = commenter
        self.comment = comment
