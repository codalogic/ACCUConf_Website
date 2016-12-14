
from flask_admin.contrib import sqla


class UserAdmin(sqla.ModelView):
    column_exclude_list = ['password']


class ProposalsAdmin(sqla.ModelView):
    column_exclude_list = ['proposer']


class PresentersAdmin(sqla.ModelView):
    pass

