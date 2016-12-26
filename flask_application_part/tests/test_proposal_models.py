"""
Test the Proposal and related models.
"""

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
    user = User(*user_data)
    proposal = Proposal(user, *proposal_data)
    presenter_data = (user.email, user.first_name, user.last_name, 'A member of the human race.', user.country, user.state)
    presenter = Presenter(*presenter_data)
    database.session.add(user)
    database.session.add(proposal)
    database.session.add(presenter)
    database.session.commit()
    proposal_presenter = ProposalPresenter(proposal.id, presenter.id, proposal, presenter, True)
    proposal.presenters.append(proposal_presenter)
    presenter.proposals.append(proposal_presenter)
    database.session.add(proposal_presenter)
    database.session.commit()
    query_result = Proposal.query.filter_by(proposer_id=user.id).all()
    assert len(query_result) == 1
    proposal = query_result[0]
    assert proposal.proposer.email == user.email
    assert (proposal.title, proposal.session_type, proposal.text) == proposal_data
    assert len(proposal.presenters) == 1
    proposal_presenter = proposal.presenters[0]
    is_lead = proposal_presenter.is_lead
    assert is_lead
    proposal_presenter = proposal_presenter.presenter
    assert (proposal_presenter.email, proposal_presenter.first_name, proposal_presenter.last_name) == (user.email, user.first_name, user.last_name)
    assert proposal.category == SessionCategory.not_sure
    assert proposal.status == ProposalState.submitted


def test_adding_review_and_comment_to_proposal_in_database(database):
    user = User(*user_data)
    proposal = Proposal(user, *proposal_data)
    presenter = Presenter(user.email, user.first_name, user.last_name, 'Someone that exists', user.country, user.state)
    database.session.add(user)
    database.session.add(proposal)
    database.session.add(presenter)
    database.session.commit()
    proposal_presenter = ProposalPresenter(proposal.id, presenter.id, proposal, presenter, True)
    proposal.presenters.append(proposal_presenter)
    presenter.proposals.append(proposal_presenter)
    database.session.add(proposal_presenter)
    score = Score(proposal, user, 10)
    comment = Comment(proposal, user, 'Perfect')
    database.session.add(score)
    database.session.add(comment)
    database.session.commit()
    query_result = Proposal.query.filter_by(proposer_id=user.id).all()
    assert len(query_result) == 1
    proposal = query_result[0]
    assert proposal.scores is not None
    assert len(proposal.scores) == 1
    assert proposal.scores[0].score == 10
    assert proposal.comments is not None
    assert len(proposal.comments) == 1
    assert proposal.comments[0].comment == 'Perfect'
