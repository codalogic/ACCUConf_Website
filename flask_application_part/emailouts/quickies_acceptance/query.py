from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import SessionType, ProposalState


def query():
    proposals = Proposal.query.filter_by(session_type=SessionType.quickie, status=ProposalState.accepted).all()
    people = tuple(p.proposer for p in proposals)
    return zip(proposals, people)


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(proposal.title)
