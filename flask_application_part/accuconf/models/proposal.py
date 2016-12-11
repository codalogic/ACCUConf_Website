from accuconf import db
from accuconf.proposals.utils.proposals import SessionType, SessionCategory, ProposalState
from accuconf.proposals.utils.schedule import ConferenceDay, SessionSlot, QuickieSlot, Track, Room


class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposer = db.Column(db.String(100), db.ForeignKey('user.id'))
    title = db.Column(db.String(150), nullable=False)
    session_type = db.Column(db.Enum(SessionType), nullable=False)
    text = db.Column(db.Text, nullable=False)
    presenters = db.relationship('ProposalPresenter', uselist=True)
    category = db.Column(db.Enum(SessionCategory), nullable=False)
    scores = db.relationship('ProposalScore', uselist=True)
    comments = db.relationship('ProposalComment', uselist=True)
    status = db.Column(db.Enum(ProposalState), nullable=False)
    # day, session, quickie_slot, track, room, slides_pdf, video_url are only non empty
    # when status is accepted.
    day = db.Column(db.Enum(ConferenceDay))
    session = db.Column(db.Enum(SessionSlot))
    quickie_slot = db.Column(db.Enum(QuickieSlot)) # Only not empty if session_type == quickie.
    track = db.Column(db.Enum(Track))
    room = db.Column(db.Enum(Room))
    slides_pdf = db.Column(db.String(80))
    video_url = db.Column(db.String(128))

    def __init__(self, proposer, title, session_type, text, category=SessionCategory.not_sure, status=ProposalState.submitted):
        self.proposer = proposer
        self.title = title
        self.session_type = session_type
        self.text = text
        self.category = SessionCategory.not_sure
        self.status = ProposalState.submitted


class ProposalPresenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    is_lead = db.Column(db.Boolean, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text(), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)

    def __init__(self, email, proposal_id, is_lead, first_name, last_name, bio, country, state):
        self.email = email
        self.proposal_id = proposal_id
        self.is_lead = is_lead
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.country = country
        self.state = state


class ProposalScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    scorer = db.Column(db.String(100), db.ForeignKey('user.id'))
    score = db.Column(db.Integer)

    def __init__(self, proposal_id, scorer, score):
        self.proposal_id = proposal_id
        self.scorer = scorer
        self.score = score


class ProposalComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    commenter = db.Column(db.String(100), db.ForeignKey('user.id'))
    comment = db.Column(db.Text)

    def __init__(self, proposal_id, commenter, comment):
        self.proposal_id = proposal_id
        self.commenter = commenter
        self.comment = comment
