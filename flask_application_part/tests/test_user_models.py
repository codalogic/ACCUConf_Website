"""
Test putting the User model into the database and getting it out again.
"""

import pytest

# PyCharm reports this as unused, but it isn't.
from common import database

from accuconf.models import User

__author__ = 'Balachandran Sivakumar, Russel Winder'
__copyright__ = '© 2016  Balachandran Sivakumar, Russel Winder'
__licence__ = 'GPLv3'

user_data = (
    'a@b.c',
    'password',
    'User',
    'Name',
    '+01234567890',
    'A human being who has done stuff',
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
    query_result = User.query.filter_by(user_id=u.user_id).all()
    assert len(query_result) == 1
    assert query_result[0] == u