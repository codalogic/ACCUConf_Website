
from flask_admin.contrib import sqla


class UserAdmin(sqla.ModelView):
    column_exclude_list = ['password']


class ProposalsAdmin(sqla.ModelView):
    pass


class PresentersAdmin(sqla.ModelView):
    pass

