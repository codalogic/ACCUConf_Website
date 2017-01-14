from accuconf.models import Proposal, Presenter, ProposalState


def query():
    acknowledged = Proposal.query.filter_by(status=ProposalState.acknowledged)
    presenters = tuple(ppp for ppp in (pp.presenter for p in acknowledged for pp in p.presenters) if ppp.bio.strip() == '')
    return tuple((None, p) for p in presenters)


def edit_template(text_file, proposal, person):
    with open(text_file) as file:
        return file.read().strip()