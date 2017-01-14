from accuconf.models import Proposal
from accuconf.proposals.utils.proposals import ProposalState


def query():
    proposals = Proposal.query.filter_by(status=ProposalState.acknowledged)
    return tuple((None, person) for person in set(pp.presenter for p in proposals for pp in p.presenters))


def edit_template(text_file, proposal, person):
    with open(text_file) as tf:
        data = tf.read().strip()
        return data.format(person.bio)
