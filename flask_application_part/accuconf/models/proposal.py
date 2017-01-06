from accuconf import db
from accuconf.proposals.utils.proposals import SessionType, SessionCategory, ProposalState, SessionAudience
from accuconf.proposals.utils.schedule import ConferenceDay, SessionSlot, QuickieSlot, Track, Room


class ProposalPresenter(db.Model):
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'), primary_key=True)
    presenter_id = db.Column(db.Integer, db.ForeignKey('presenter.id'), primary_key=True)
    proposal = db.relationship('Proposal', back_populates='presenters')
    presenter = db.relationship('Presenter', back_populates='proposals')
    is_lead = db.Column(db.Boolean, nullable=False)

    #  When using an association object rather than just an association table, it seems
    #  the keys have to be set manually. This likely indicates something wrong with
    #  this code as this has never had to be done in other cases. this just seems wrong.
    #
    # TODO Fix this.
    def __init__(self, proposal_id, presenter_id, proposal, presenter, is_lead):
        self.proposal_id = proposal_id
        self.presenter_id = presenter_id
        self.proposal = proposal
        self.presenter = presenter
        self.is_lead = is_lead


class Proposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    proposer = db.relationship('User', back_populates='proposals')
    title = db.Column(db.String(150), nullable=False)
    session_type = db.Column(db.Enum(SessionType), nullable=False)
    text = db.Column(db.Text, nullable=False)
    presenters = db.relationship(ProposalPresenter, back_populates='proposal')
    audience = db.Column(db.Enum(SessionAudience), nullable=False)
    category = db.Column(db.Enum(SessionCategory), nullable=False)
    scores = db.relationship('Score', backref='proposal')
    comments = db.relationship('Comment', backref='proposal')
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

    def __init__(self, proposer, title, session_type, text,
                 audience=SessionAudience.all, category=SessionCategory.not_sure, status=ProposalState.submitted,
                 day=None, session=None, quickie_slot=None, track=None, room=None,
                 slides_pdf=None, video_url=None):
        self.proposer = proposer
        self.title = title
        self.session_type = session_type
        self.text = text
        self.audience = audience
        self.category = category
        self.status = status
        self.day = day
        self.session = session
        self.quickie_slot = quickie_slot
        self.track = track
        self.room = room
        self.slides_pdf = slides_pdf
        self.video_url = video_url


class Presenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text(), nullable=False)
    country = db.Column(db.String(100), nullable=False)  # TODO Should be String(5)
    state = db.Column(db.String(100), nullable=False)  # TODO Should be String(10)
    proposals = db.relationship(ProposalPresenter, back_populates='presenter')

    def __init__(self, email, first_name, last_name, bio, country, state):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.country = country
        self.state = state


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    scorer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)

    def __init__(self, proposal, scorer, score):
        self.proposal = proposal
        self.scorer = scorer
        self.score = score


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposal.id'))
    commenter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment = db.Column(db.Text)

    def __init__(self, proposal, commenter, comment):
        self.proposal = proposal
        self.commenter = commenter
        self.comment = comment
