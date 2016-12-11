'''
This tests that we are correctly accessing the Werkzeug test client of the application.
'''

from common import client, get_and_check_content


def test_getting_werkzeug_test_client_and_the_top_static_pages(client):
    assert client is not None
    get_and_check_content(client, '/', 302, ('Redirecting', '/site/index.html'))
    get_and_check_content(client, '/site/index.html', 200, ('ACCU',))
