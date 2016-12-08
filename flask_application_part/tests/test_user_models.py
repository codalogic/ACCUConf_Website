"""
Test the User model.
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

parameter_names = ('user_id', 'password', 'first_name', 'last_name', 'phone', 'bio', 'country', 'state', 'postal_code', 'town_city', 'street_address')

type_error_messages = tuple('{} must be a string value.'.format(p) for p in parameter_names)

value_error_messages = tuple('{} cannot be an empty string.'.format(p) for p in parameter_names)


def test_user_construction():
    user = User(*user_data)
    assert user is not None
    assert (
        user.user_id,
        user.password,
        user.first_name,
        user.last_name,
        user.phone,
        user.bio,
        user.country,
        user.state,
        user.postal_code,
        user.town_city,
        user.street_address,
    ) == user_data


@pytest.mark.parametrize('index', range(len(user_data)))
def test_user_none_value(index):
    with pytest.raises(TypeError) as ex:
        data = list(user_data)
        data[index] = None
        User(*data)
    assert type_error_messages[index] in str(ex.value)


@pytest.mark.parametrize('index', range(len(user_data)))
def test_user_not_a_string_value(index):
    with pytest.raises(TypeError) as ex:
        data = list(user_data)
        data[index] = 1
        User(*data)
    assert type_error_messages[index] in str(ex.value)


@pytest.mark.parametrize('index', range(len(user_data)))
def test_user_empty_string_value(index):
    with pytest.raises(ValueError) as ex:
        data = list(user_data)
        data[index] = ''
        User(*data)
    assert value_error_messages[index] in str(ex.value)


def test_user_in_database(database):
    u = User(*user_data)
    database.session.add(u)
    database.session.commit()
    query_result = User.query.filter_by(user_id=u.user_id).all()
    assert len(query_result) == 1
    assert query_result[0] == u