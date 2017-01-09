from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import ProposalState


def query():
    proposals = Proposal.query.filter_by(status=ProposalState.accepted)
    people = tuple(p.proposer for p in proposals)
    return zip(proposals, people)


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(proposal.title)
