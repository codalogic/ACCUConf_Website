"""
Tests for submitting a proposal.
"""

import json

import pytest

from common import client, get_and_check_content, post_and_check_content

from accuconf.models import User, Proposal
from accuconf.proposals.utils.proposals import SessionType

__author__ = 'Balachandran Sivakumar, Russel Winder'
__copyright__ = '© 2016  Balachandran Sivakumar, Russel Winder'
__licence__ = 'GPLv3'


@pytest.fixture(scope='function')
def registration_data():
    return {
        'usermail': 'a@b.c',
        'password': 'Password1',
        'cpassword': 'Password1',
        'firstname': 'User',
        'lastname': 'Name',
        'phone': '+011234567890',
        'pincode': '123456',
        'country': 'India',
        'state': 'TamilNadu',
        'towncity': 'Chennai',
        'streetaddress': 'Chepauk',
        'captcha': '1',
        'question': '12',
    }


# TODO How come the following user data are OK without many of the fields


@pytest.fixture(scope='function')
def proposal_single_presenter():
    return {
        'proposer': 'a@b.c',
        'title': 'ACCU Proposal',
        'session_type': 'quickie',
        'abstract': '''This is a test proposal that will have
dummy data. Also this is not a very
lengthy proposal''',
        'presenters': [
            {
                'email': 'a@b.c',
                'lead': 1,
                'fname': 'User',
                'lname': 'Name',
                'bio': 'A nice member of the human race.',
                'country': 'India',
                'state': 'TamilNadu'
            },
        ]
    }


@pytest.fixture(scope='function')
def proposal_multiple_presenters_single_lead():
    return {
        'proposer': 'a@b.c',
        'title': 'ACCU Proposal',
        'session_type': 'miniworkshop',
        'abstract': ''' This is a test proposal that will have
dummy data. Also this is not a very
lengthy proposal''',
        'presenters': [
            {
                'email': 'a@b.c',
                'lead': 1,
                'fname': 'User',
                'lname': 'Name',
                'bio': 'A person.',
                'country': 'India',
                'state': 'TamilNadu'
            },
            {
                'email': 'p2@b.c',
                'lead': 0,
                'fname': 'Presenter',
                'lname': 'Second',
                'bio': 'Another person',
                'country': 'India',
                'state': 'TamilNadu'
            },
        ]
    }


@pytest.fixture(scope='function')
def proposal_multiple_presenters_and_leads():
    return {
        'proposer': 'a@b.c',
        'title': 'ACCU Proposal',
        'session_type': 'workshop',
        'abstract': ''' This is a test proposal that will have
dummy data. Also this is not a very
lengthy proposal''',
        'presenters': [
            {
                'email': 'a@b.c',
                'lead': 1,
                'fname': 'User',
                'lname': 'Name',
                'bio': 'A human being',
                'country': 'India',
                'state': 'TamilNadu'
            },
            {
                'email': 'p2@b.c',
                'lead': 1,
                'fname': 'Presenter',
                'lname': 'Second',
                'bio': 'Someone who is human.',
                'country': 'India',
                'state': 'TamilNadu'
            },
        ]
    }


def test_user_can_register(client, registration_data):
    post_and_check_content(client, '/proposals/register', registration_data, values=('You have successfully registered',))


def test_user_cannot_register_twice(client, registration_data):
    test_user_can_register(client, registration_data)
    post_and_check_content(client, '/proposals/register', registration_data, values=('Registration failed',))


def test_registered_user_can_login(client, registration_data):
    test_user_can_register(client, registration_data)
    post_and_check_content(client, '/proposals/login', {'usermail': registration_data['usermail'], 'password': registration_data['password']}, code=302, values=('Redirecting',))
    get_and_check_content(client, '/site/index.html', values=('ACCU Conference',))
    # TODO How to check in the above that the left-side menu now has the proposals links?


def test_logged_in_user_can_get_submission_page(client, registration_data):
    test_registered_user_can_login(client, registration_data)
    get_and_check_content(client, '/proposals/submit_proposal', values=('Submit a proposal',))


def test_logged_in_user_can_submit_a_single_presenter_proposal(client, registration_data, proposal_single_presenter):
    test_registered_user_can_login(client, registration_data)
    # TODO Why do we have to send JSON here but just used dictionaries previously?
    rvd = post_and_check_content(client, '/proposals/upload_proposal', json.dumps(proposal_single_presenter), 'application/json', values=('success',))
    response = json.loads(rvd)
    assert response['success']
    user = User.query.filter_by(email='a@b.c').all()
    assert len(user) == 1
    user = user[0]
    assert user is not None
    proposal = Proposal.query.filter_by(proposer=user.id).all()
    assert len(proposal) == 1
    proposal = proposal[0]
    assert proposal is not None
    assert user.proposals is not None
    assert len(user.proposals) == 1
    p = user.proposals[0]
    assert len(p.presenters) == 1
    assert p.presenters[0].email == user.email
    assert proposal.session_type == SessionType.quickie


def test_logged_in_user_can_submit_multipresenter_single_lead_proposal(client, registration_data, proposal_multiple_presenters_single_lead):
    test_registered_user_can_login(client, registration_data)
    # TODO Why do we have to send JSON here but just used dictionaries previously?
    rvd = post_and_check_content(client, '/proposals/upload_proposal', json.dumps(proposal_multiple_presenters_single_lead), 'application/json', values=('success',))
    response = json.loads(rvd)
    assert response['success']
    user = User.query.filter_by(email='a@b.c').all()
    assert len(user) == 1
    user = user[0]
    assert user is not None
    proposal = Proposal.query.filter_by(proposer=user.id).all()
    assert len(proposal) == 1
    proposal = proposal[0]
    assert proposal is not None
    assert user.proposals is not None
    p = user.proposals[0]
    assert len(p.presenters) == 2
    assert p.presenters[0].email == user.email
    assert proposal.session_type == SessionType.miniworkshop


def test_logged_in_user_cannot_submit_multipresenter_multilead_proposal(client, registration_data, proposal_multiple_presenters_and_leads):
    test_registered_user_can_login(client, registration_data)
    # TODO Why do we have to send JSON here but just used dictionaries previously?
    rvd = post_and_check_content(client, '/proposals/upload_proposal', json.dumps(proposal_multiple_presenters_and_leads), 'application/json', values=('success',))
    response = json.loads(rvd)
    assert response["success"] is False
    assert "message" in response
    assert "both marked as lead presenters" in response["message"]
    user = User.query.filter_by(email='a@b.c').all()
    assert len(user) == 1
    user = user[0]
    assert user is not None
    assert len(user.proposals) == 0
    proposal = Proposal.query.filter_by(proposer=user.id).all()
    assert len(proposal) == 0
