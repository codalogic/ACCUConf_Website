"""
Various bits of code used in various places. It is assumed this file is imported into all tests.
"""

import pytest
import sys
from pathlib import PurePath

from selenium import webdriver

path_to_add = str(PurePath(__file__).parent.parent)
if path_to_add not in sys.path:
    sys.path.insert(0, path_to_add)

from accuconf import app, db


@pytest.fixture
def browser():
    driver = webdriver.PhantomJS()
    yield driver
    driver.quit()


@pytest.fixture
def database():
    db.drop_all()
    db.create_all()
    yield db
    db.drop_all()


base_url = 'http://localhost:8000/'
