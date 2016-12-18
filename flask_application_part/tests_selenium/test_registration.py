from common import app, browser, database, base_url


def test_can_get_root(browser):
    browser.get(base_url)
    assert 'ACCU Conference' in browser.page_source


def test_can_get_login_page(browser):
    browser.get(base_url + 'site/login/')
    if (app.config['CALL_OPEN'] or app.config['REVIEWING_ALLOWED']) and not app.config['MAINTENANCE']:
        assert 'Login' in browser.page_source
    else:
        assert '404 Not Found' in browser.page_source