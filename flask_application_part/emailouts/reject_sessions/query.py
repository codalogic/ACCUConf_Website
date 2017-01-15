from sqlalchemy import and_, or_

from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import ProposalState, SessionType


def query():
    proposals = Proposal.query.filter(
        and_(
            or_(
                Proposal.session_type == SessionType.session,
                Proposal.session_type == SessionType.workshop,
                Proposal.session_type == SessionType.miniworkshop,
                Proposal.session_type == SessionType.quickie,
            ),
            or_(
                Proposal.status == ProposalState.submitted,
                Proposal.status == ProposalState.rejected,
            )
        )
    )
    return tuple((proposal, proposal.proposer) for proposal in proposals )


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(proposal.title)
