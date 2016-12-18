from flask_admin.contrib.sqla import ModelView
from flask_admin.form.fields import Select2Field

# There are some blocking problem with Enums, SQLAlchemy and Flask-Admin
# editing dialogues: The edit dialogue doesn't pick up the data it picks up the
# first item of the enum. cf.  https://github.com/mrjoes/flask-admin/issues/33#issuecomment-267345348
# and https://github.com/flask-admin/flask-admin/issues/1315 (the latter being in
# the mainline repository). Here we use an amendment of mrjoes workaround.
#
# TODO Hassle the maintainers to fix this and then remove the workarounds.


from accuconf.proposals.utils.proposals import SessionType, ProposalState, SessionCategory, SessionAudience
from accuconf.proposals.utils.schedule import ConferenceDay, SessionSlot, QuickieSlot, Track, Room


def _create_enum_selector(enum_class, default):
    class EnumSelect2Field(Select2Field):
        def pre_validate(self, form):
            for v, _ in self.choices:
                if self.data == self.coerce(v):
                    break
            else:
                raise ValueError('{} is not a valid choice'.format(v))
            #super().pre_validate(form)  # Is this needed?

    return EnumSelect2Field(
            choices=[(x.name, x.value) for x in enum_class],
            coerce=enum_class,
            default=default)


class UserAdmin(ModelView):
    column_exclude_list = ['password']


class ProposalsAdmin(ModelView):
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
    form_columns = (
        'title',
        'x_audience',
        'x_category',
        'x_status',
        'x_day',
        'x_session',
        'x_quickie_slot',
        'x_track',
        'x_room',
        'slides_pdf',
        'video_url',
    )
    form_extra_fields = {
        'x_session_type': _create_enum_selector(SessionType, SessionType.session),
        'x_audience': _create_enum_selector(SessionAudience, SessionAudience.all),
        'x_category': _create_enum_selector(SessionCategory, SessionCategory.not_sure),
        'x_status': _create_enum_selector(ProposalState, ProposalState.submitted),
        'x_day': _create_enum_selector(ConferenceDay, ConferenceDay.day_1),
        'x_session': _create_enum_selector(SessionSlot, SessionSlot.session_1),
        'x_quickie_slot': _create_enum_selector(QuickieSlot, QuickieSlot.slot_1),
        'x_track': _create_enum_selector(Track, Track.other),
        'x_room': _create_enum_selector(Room, Room.bristol_1),
    }


class PresentersAdmin(ModelView):
    pass
