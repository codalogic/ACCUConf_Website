from flask_admin.contrib import sqla


class UserAdmin(sqla.ModelView):
    column_exclude_list = ['password']


class ProposalsAdmin(sqla.ModelView):
    column_list = [
        'proposer.first_name',
        'proposer.last_name',
        'title',
        'session_type',
        'audience',
        'category',
        'status',
        'day',
        'session',
        'quickie_slot',
        'track',
        'room',
        'slides_pdf',
        'video_url',
    ]


class PresentersAdmin(sqla.ModelView):
    pass
