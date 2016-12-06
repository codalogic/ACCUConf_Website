"""
Test the basic proposal model.
"""

# import the fixture, PyCharm believes it isn't a used symbol, but it is.
from common import database

from accuconf.models import User, Proposal, ProposalPresenter
from accuconf.proposals.utils.proposals import SessionType, ProposalState

__author__ = 'Balachandran Sivakumar, Russel Winder'
__copyright__ = '© 2016  Balachandran Sivakumar, Russel Winder'
__licence__ = 'GPLv3'


def test_proposal_basic(database):
    u = User(
        "abc@b.c",
        "password",
        'User',
        'Name',
        '+01234567890',
        'A member of the human race.',
        "IND",
        "KARNATAKA",
        "560093",
        'Town',
        'Address',
    )
    p = Proposal(
        "a@b.c",
        "TDD with C++",
        SessionType.quickie,
        "AABBCC",
    )
    presenter = ProposalPresenter(
        p.id,
        u.user_id,
        True,
        u.first_name,
        u.last_name,
        u.country,
        u.state,
    )
    p.presenters = [presenter]
    p.session_proposer = u
    p.lead_presenter = u
    u.proposal = p
    database.session.add(u)
    database.session.add(p)
    database.session.add(presenter)
    database.session.commit()

    p = User.query.filter_by(user_id="abc@b.c").first().proposal
    assert p.status == ProposalState.submitted
