"""
Test putting the User model into the database and getting it out again.
"""

import pytest

# PyCharm reports this as unused, but it isn't.
from common import database

from accuconf.models import User

user_data = (
    'a@b.c',
    'password',
    'User',
    'Name',
    '+01234567890',
    'Some Country',
    'Some State',
    'Postcode',
    'Town or City',
    'Street Address',
)


def test_user_in_database(database):
    u = User(*user_data)
    database.session.add(u)
    database.session.commit()
    query_result = User.query.filter_by(email=u.email).all()
    assert len(query_result) == 1
    assert query_result[0] == u