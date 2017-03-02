"""
Various bits of code used in various places. It is assumed this file is imported into all tests.
"""

import pytest
import sys

from pathlib import PurePath

path_to_add = str(PurePath(__file__).parent.parent)
if path_to_add not in sys.path:
    sys.path.insert(0, path_to_add)

from accuconf import app, db


@pytest.fixture
def database():
    """
    Deliver up the database associated with the application.
    """
    app.config['TESTING'] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db
        db.drop_all()


@pytest.fixture(scope='function')
def client():
    """
    A Werkzeug client in testing mode with a newly created database.
    """
    app.config['TESTING'] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.drop_all()


def get_and_check_content(client, url, code=200, values=()):
    """
    Send a get to the client with the url, check that allthe values are in the returned HTML.
    """
    rv = client.get(url)
    assert rv is not None
    assert rv.status_code == code, '######## Status code was {}, expected {}'.format(rv.status_code, code)
    rvd = rv.get_data().decode('utf-8')
    for item in values:
        assert item in rvd # , '######## `{}` not in\n{}'.format(item, rvd)
    return rvd


def post_and_check_content(client, url, data, content_type=None, code=200, values=(), follow_redirects=False):
    """
    Send a post to the client with the url and data, of the content_type, and the check that all the values
    are in the returned HTML.
    """
    rv = client.post(url, data=data, content_type=content_type, follow_redirects=follow_redirects)
    assert rv is not None
    assert rv.status_code == code, '######## Status code was {}, expected {}'.format(rv.status_code, code)
    rvd = rv.get_data().decode('utf-8')
    for item in values:
        assert item in rvd # , '######## `{}` not in\n{}'.format(item, rvd)
    return rvd
