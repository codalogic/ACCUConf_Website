"""
Classes to define the states of the application.
"""

from pathlib import Path


class _Base:
    here = Path(__file__).parent
    database_path = here.parent / 'accuconf.db'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DEBUG = False
    TESTING = False
    SECRET_KEY = "TheObviouslyOpenSecret"
    NIKOLA_STATIC_PATH = here / 'static'
    MAINTENANCE = False
    CALL_OPEN = False
    REVIEWING_ALLOWED = False
    ADMINISTERING = False
    API_ACCESS = False


class ApplicationOff(_Base):
    pass


class CallForProposalsOpen(_Base):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(_Base.database_path)
    CALL_OPEN = True
    REVIEWING_ALLOWED = True


class CallForProposalsOpenMaintenance(CallForProposalsOpen):
    MAINTENANCE = True


class ReviewingOnly(_Base):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(_Base.database_path)
    REVIEWING_ALLOWED = True


class ReviewingOnlyMaintenance(CallForProposalsOpen):
    MAINTENANCE = True


class TestingWithDatabase(_Base):
    database_path = _Base.here.parent / 'accuconf_test.db'
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(database_path)
    DEBUG = True
    TESTING = True
    CALL_OPEN = True
    REVIEWING_ALLOWED = True


class TestingWithDatabaseMaintenance(TestingWithDatabase):
    MAINTENANCE = True


class AdministeringDatabase(_Base):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(_Base.database_path)
    MAINTENANCE = True
    ADMINISTERING = True


class APIAccessOpen(_Base):
    database_path = _Base.here.parent / 'accuconf_api.db'
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(database_path)
    API_ACCESS = True


Config = ApplicationOff
