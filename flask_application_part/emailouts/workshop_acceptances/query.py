from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import SessionType, ProposalState


def query():
    return Proposal.query.filter_by(session_type=SessionType.fulldayworkshop, status=ProposalState.accepted).all()


def edit_template(text_file, proposal):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(proposal.title)
