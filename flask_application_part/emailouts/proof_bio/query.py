from sqlalchemy import and_, or_

from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import SessionType, ProposalState


def query():
    proposals = Proposal.query.filter(
        and_(
            Proposal.status == ProposalState.acknowledged,
            or_(
                Proposal.session_type == SessionType.session,
                Proposal.session_type == SessionType.miniworkshop,
                Proposal.session_type == SessionType.workshop,
            ),
        )
    )
    return tuple((None, person) for person in (pp.presenter for p in proposals for pp in p.presenters))


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(person.bio)
