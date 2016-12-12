"""
Classes to define the states of the application.
"""

from pathlib import Path


class _Base:
    here = Path(__file__).parent
    database_path = None
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DEBUG = False
    TESTING = False
    SECRET_KEY = "TheObviouslyOpenSecret"
    NIKOLA_STATIC_PATH = here / 'static'
    MAINTENANCE = False
    CALL_OPEN = False


class CallForProposalsClosed(_Base):
    pass


class CallForProposalsOpen(_Base):
    database_path = _Base.here.parent / 'accuconf.db'
    CALL_OPEN = True


class CallForProposalsOpenMaintenance(CallForProposalsOpen):
    MAINTENANCE = True


class TestingWithDatabase(_Base):
    database_path = _Base.here.parent / 'accuconf_test.db'
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(database_path)
    DEBUG = True
    TESTING = True


class TestingWithDatabaseMaintenance(TestingWithDatabase):
    MAINTENANCE = True


class AdministeringDatabase(_Base):
    database_path = _Base.here.parent / 'accuconf.db'
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(database_path)


Config = CallForProposalsClosed