import pytest

from common import client, post_and_check_content


@pytest.fixture
def registrant():
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
        'towncity' : 'Chennai',
        'streetaddress': 'Chepauk',
        'captcha': '1',
        'question': '12',
    }


def test_user_reg_basic(client, registrant):
    post_and_check_content(client, '/proposals/register', registrant, values=('You have successfully registered', 'Please login'))


def test_user_reg_dup(client, registrant):
    test_user_reg_basic(client, registrant)
    post_and_check_content(client, '/proposals/register', registrant, values=('Duplicate user email',))


def test_password_short(client):
    post_and_check_content(client, '/proposals/register', {
        'usermail': 'test@std.dom',
        'password': 'Pass1',
        'cpassword': 'Pass1',
        'firstname': 'User2',
        'lastname': 'Name2',
        'phone': '+011234567890',
        'pincode': '123456',
        'country': 'India',
        'state': 'TamilNadu',
        'towncity' : 'Chennai',
        'streetaddress': 'Chepauk',
        'captcha': '1',
        'question': '12',
    }, values=('Password did not meet checks',))


def test_password_invalid(client):
    post_and_check_content(client, '/proposals/register', {
        'usermail': 'test@std.dom',
        'password': 'password',
        'cpassword': 'password',
        'firstname': 'User2',
        'lastname': 'Name2',
        'phone': '+011234567890',
        'pincode': '123456',
        'country': 'India',
        'state': 'TamilNadu',
        'towncity' : 'Chennai',
        'streetaddress': 'Chepauk',
        'bio': 'An individual of the world.',
        'captcha': '1',
        'question': '12'
    }, values=('Password did not meet checks',))


def test_username_invalid(client):
    post_and_check_content(client, '/proposals/register', {
        'usermail': 'testing.test.dom',
        'password': 'passworD13',
        'cpassword': 'passworD13',
        'firstname': 'User2',
        'lastname': 'Name2',
        'phone': '+011234567890',
        'pincode': '123456',
        'country': 'India',
        'state': 'TamilNadu',
        'towncity' : 'Chennai',
        'streetaddress': 'Chepauk',
        'bio': 'An individual of the world.',
        'captcha': '1',
        'question': '12',
    }, values=('Invalid/Duplicate user email',))
