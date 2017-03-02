from sqlalchemy import and_, or_

from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import ProposalState, SessionType


def query():
    proposals = Proposal.query.filter(
        and_(
            Proposal.status == ProposalState.acknowledged,
            or_(
                Proposal.session_type == SessionType.quickie,
                Proposal.session_type == SessionType.session,
            )
        )
    )
    return tuple((proposal, person.presenter) for proposal in proposals for person in proposal.presenters)


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        return tf.read().strip()
