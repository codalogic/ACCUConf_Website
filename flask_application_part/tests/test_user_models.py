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

error_messages = (
    'user_id cannot be None or empty.',
    'Password should have at least 8 letters/numbers.',
    'first_name cannot be None or empty.',
    'last_name cannot be None or empty.',
    'phone cannot be None or empty.',
    'bio cannot be None or empty.',
    'country cannot be None or empty.',
    'state cannot be None or empty.',
    'postal_code cannot be None or empty.',
    'town_city cannot be None or empty.',
    'street_address cannot be None or empty.',
)


def test_user_basic():
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
def test_user_null_field(index):
    with pytest.raises(AttributeError) as ex:
        data = list(user_data)
        data[index] = None
        User(*data)
    assert error_messages[index] in str(ex.value)


@pytest.mark.parametrize('index', range(len(user_data)))
def test_user_empty_field(index):
    with pytest.raises(AttributeError) as ex:
        data = list(user_data)
        data[index] = ''
        User(*data)
    assert error_messages[index] in str(ex.value)


def test_basic(database):
    u = User(*user_data)
    database.session.add(u)
    database.session.commit()
    assert User.query.filter_by(user_id=u.user_id).first() == u
