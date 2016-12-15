from common import browser, database, base_url


def test_can_get_root(browser, database):
    browser.get(base_url)
    assert 'ACCU Conference' in browser.page_source
