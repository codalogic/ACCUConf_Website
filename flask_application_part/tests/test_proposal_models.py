"""
Test the Proposal and related models.
"""

import pytest

# import the fixture, PyCharm believes it isn't a used symbol, but it is.
from common import database

from accuconf.models import User, Proposal, ProposalPresenter
from accuconf.proposals.utils.proposals import SessionType, SessionCategory, ProposalState

__author__ = 'Balachandran Sivakumar, Russel Winder'
__copyright__ = '© 2016  Balachandran Sivakumar, Russel Winder'
__licence__ = 'GPLv3'

user_data = (
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

type_error_messages = (
    'proposer must be a string value.',
    'title must be a string value.',
    'session_type must be a SessionType value.',
    'text must be a string value.',
    'category must be a SessionCategory value.',
    'status must be a ProposalState value.',
)

value_error_messages= tuple('{} cannot be an empty string.'.format(p) for p in ('proposer', 'title', '', 'text'))

proposal_data = (
    user_data[0],
    "TDD with C++",
    SessionType.quickie,
    "AABBCC",
)


def test_proposal_construction():
    proposal = Proposal(*proposal_data)
    assert proposal is not None
    assert (
        proposal.proposer,
        proposal.title,
        proposal.session_type,
        proposal.text,
    ) == proposal_data
    assert proposal.category == SessionCategory.not_sure
    assert proposal.status == ProposalState.submitted


@pytest.mark.parametrize('index', range(len(proposal_data)))
def test_proposal_null_value(index):
    with pytest.raises(TypeError) as ex:
        data = list(proposal_data)
        data[index] = None
        Proposal(*data)
    assert type_error_messages[index] in str(ex.value)


@pytest.mark.parametrize('index', range(len(proposal_data)))
def test_proposal_empty_string(index):
    data = list(proposal_data)
    data[index] = ''
    if index == 2:
        with pytest.raises(TypeError) as ex:
            Proposal(*data)
        assert type_error_messages[index] in str(ex.value)
    else:
        with pytest.raises(ValueError) as ex:
            Proposal(*data)
        assert value_error_messages[index] in str(ex.value)


def test_proposal_in_database(database):
    u = User(*user_data)
    p = Proposal(*proposal_data)
    presenter_data = (
        p.id,
        u.user_id,
        True,
        u.first_name,
        u.last_name,
        u.country,
        u.state,
    )
    presenter = ProposalPresenter(*presenter_data)
    p.presenters = [presenter]
    p.lead_presenter = u
    u.proposal = p
    database.session.add(u)
    database.session.add(p)
    database.session.add(presenter)
    database.session.commit()
    query_result = Proposal.query.filter_by(proposer=u.user_id).all()
    assert len(query_result) == 1
    p = query_result[0]
    assert (
        p.proposer,
        p.title,
        p.session_type,
        p.text,
    ) == proposal_data
    assert len(p.presenters) == 1
    presenter = p.presenters[0]
    assert (
        presenter.email,
        presenter.first_name,
        presenter.last_name,
    ) == (
        u.user_id,
        u.first_name,
        u.last_name,
    )
    assert p.category == SessionCategory.not_sure
    assert p.status == ProposalState.submitted
