"""
Test the Proposal and related models.
"""

import pytest

# import the fixture, PyCharm believes it isn't a used symbol, but it is.
from common import database

from accuconf.models import User, Proposal, Presenter, ProposalPresenter, Score, Comment
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
    "IND",
    "KARNATAKA",
    "560093",
    'Town',
    'Address',
)

proposal_data = (
    "TDD with C++",
    SessionType.quickie,
    "A session about creating C++ programs with proper process.",
)


def test_putting_proposal_in_database(database):
    u = User(*user_data)
    p = Proposal(u, *proposal_data)
    presenter_data = (u.email, u.first_name, u.last_name, 'A member of the human race.', u.country, u.state)
    presenter = ProposalPresenter(Presenter(*presenter_data), True)
    p.presenters.append(presenter)
    database.session.add(u)
    database.session.add(p)
    database.session.add(presenter)
    database.session.commit()
    query_result = Proposal.query.filter_by(proposer_id=u.id).all()
    assert len(query_result) == 1
    p = query_result[0]
    assert p.proposer.email == u.email
    assert (p.title, p.session_type, p.text) == proposal_data
    assert len(p.presenters) == 1
    proposal_presenter = p.presenters[0]
    is_lead = proposal_presenter.is_lead
    assert is_lead
    presenter = proposal_presenter.presenter
    assert (presenter.email, presenter.first_name, presenter.last_name) == (u.email, u.first_name, u.last_name)
    assert p.category == SessionCategory.not_sure
    assert p.status == ProposalState.submitted


def test_adding_review_and_comment_to_proposal_in_database(database):
    u = User(*user_data)
    p = Proposal(u, *proposal_data)
    presenter = ProposalPresenter(Presenter(u.email, u.first_name, u.last_name, 'Someone that exists', u.country, u.state), True)
    score = Score(p, u, 10)
    comment = Comment(p, u, 'Perfect')
    p.presenters.append(presenter)
    database.session.add(u)
    database.session.add(p)
    database.session.add(presenter)
    database.session.add(score)
    database.session.add(comment)
    database.session.commit()
    query_result = Proposal.query.filter_by(proposer_id=u.id).all()
    assert len(query_result) == 1
    p = query_result[0]
    assert p.scores is not None
    assert len(p.scores) == 1
    assert p.scores[0].score == 10
    assert p.comments is not None
    assert len(p.comments) == 1
    assert p.comments[0].comment == 'Perfect'
