from sqlalchemy import and_, or_

from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import SessionType, ProposalState


def query():
    proposals = Proposal.query.filter(
        and_(
            Proposal.status == ProposalState.accepted,
            or_(
                Proposal.session_type == SessionType.session,
                Proposal.session_type == SessionType.miniworkshop,
                Proposal.session_type == SessionType.workshop,
            ),
        )
    )
    people = tuple(p.proposer for p in proposals)
    return zip(proposals, people)


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(proposal.title)
