from sqlalchemy import and_

from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import ProposalState, SessionType


def query():
    proposals = Proposal.query.filter(
        and_(
            Proposal.status == ProposalState.acknowledged,
            Proposal.session_type == SessionType.session,
        )
    )
    return tuple((None, person) for person in set(pp.presenter for p in proposals for pp in p.presenters))


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        return tf.read().strip()
