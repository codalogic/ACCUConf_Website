from enum import Enum


class SessionType(Enum):
    fulldayworkshop = 'fulldayworkshop'
    session = 'session'
    miniworkshop = 'miniworkshop'
    workshop = 'workshop'
    quickie = 'quickie'
    keynote = 'keynote'


sessiontype_descriptions = {
    SessionType.fulldayworkshop: 'A full day, pre-conference workshop.',
    SessionType.session: 'A 90 minute presentation session with questions.',
    SessionType.miniworkshop: 'A 90 minute workshop with active attender participation.',
    SessionType.workshop: 'A 180 minute workshop with active attender participation.',
    SessionType.quickie: 'A 15 minute presentation.',
    SessionType.keynote: 'A 60 minute keynote presentation.',
}


class ProposalState(Enum):
    submitted = 'submitted'
    accepted = 'accepted'
    acknowledged = 'acknowledged'
    rejected = 'rejected'
    backup = 'backup'
    withdrawn = 'withdrawn'


class SessionCategory(Enum):
    cpp = 'cpp'
    agile = 'agile'
    tools = 'tools'
    not_sure = 'not_sure'


class SessionAudience(Enum):
    beginner = 'beginner'
    intermediate = 'intermediate'
    expert = 'expert'
    all = 'all'
