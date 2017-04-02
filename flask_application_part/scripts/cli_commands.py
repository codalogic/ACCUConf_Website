"""
This module provides all the additional CLI commands.
"""

import json
import os
import re
import shutil
import sys

from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from statistics import mean, median

from email.mime.text import MIMEText
from email.utils import formatdate
from smtplib import SMTP

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, KeepTogether
from reportlab.platypus.flowables import HRFlowable

# This must be imported here even though it may not be explicitly used in this file.
import click

file_directory = Path(__file__).absolute().parent
sys.path.insert(0, str(file_directory.parent))

from accuconf import app, db
from accuconf.models import User, ProposalPresenter, Proposal, Presenter, Score, Comment
from accuconf.proposals.utils.proposals import SessionType, ProposalState, SessionCategory, SessionAudience
from accuconf.proposals.utils.schedule import ConferenceDay, SessionSlot, QuickieSlot, Track, Room
from accuconf.proposals.utils.roles import Role

start_date = date(2017, 4, 25)  # The day of the full-day pre-conference workshops

@app.cli.command()
def create_database():
    """
    Create an initial database.
    """
    db.create_all()


@app.cli.command()
def all_reviewers():
    """
    Print a list of all the registrants labelled as a reviewers.
    """
    for x in User.query.filter_by(role=Role.reviewer).all():
        print('{} {} <{}>'.format(x.first_name, x.last_name, x.user_id))


@app.cli.command()
@click.argument('committee_email_file_path')
def are_committee_all_reviewers(committee_email_file_path):
    """
    Ensure consistency between committee list and reviewers list.
    """
    try:
        with open(committee_email_file_path) as committee_email_file:
            committee_emails = {s.strip() for s in committee_email_file.read().split()}
            reviewer_emails = {u.email for u in User.query.filter_by(role=Role.reviewer).all()}
            committee_not_reviewer = {c for c in committee_emails if c not in reviewer_emails}
            reviewers_not_committee = {r for r in reviewer_emails if r not in committee_emails}
            print('Committee members not reviewers:')
            for p in committee_not_reviewer:
                print('\t', p)
            print('Reviewers not committee members:')
            for p in reviewers_not_committee:
                print('\t', p)
    except FileNotFoundError:
        print('{} not found.'.format(committee_email_file_path))


@app.cli.command()
@click.argument('committee_email_file_path')
def set_committee_as_reviewers(committee_email_file_path):
    """
    Update database to ensure all committee members are reviewers.
    """
    try:
        with open(committee_email_file_path) as committee_email_file:
            committee_emails = {s.strip() for s in committee_email_file.read().split()}
            reviewer_emails = {u.email for u in User.query.filter_by(role=Role.reviewer).all()}
            committee_not_reviewer = {c for c in committee_emails if c not in reviewer_emails}
            print('Setting these Committee members as reviewers:')
            for p in committee_not_reviewer:
                user = User.query.filter_by(email=p).all()
                if len(user) == 0:
                    print('\t ####', p, 'not found')
                elif len(user) > 1:
                    print('\t ####', p, 'has more that one entry, this cannot be.')
                else:
                    user = user[0]
                    print('\t', user.first_name, user.last_name, '–', user.email)
                    user.role = Role.reviewer
                    db.session.commit()
    except FileNotFoundError:
        print('{} not found.'.format(committee_email_file_path))


@app.cli.command()
def create_proposal_sheets():
    """
    Create the bits of papers for constructing an initial schedule.
    """
    file_path = str(file_directory.parent / 'proposal_sheets.pdf')
    style_sheet = getSampleStyleSheet()['BodyText']
    style_sheet.fontSize = 18
    style_sheet.leading = 22
    document = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=10, bottomMargin=30)
    elements = []
    for p in Proposal.query.all():
        scores = tuple(score.score for score in p.scores if score.score != 0)
        table = Table([
            [Paragraph(p.title, style_sheet), p.session_type],
            [', '.join('{} {}'.format(pp.first_name, pp.last_name) for pp in p.presenters),
             ', '.join(str(score.score) for score in p.scores) + ' — {:.2f}, {}'.format(mean(scores), median(scores)) if len(scores) > 0 else ''],
        ], colWidths=(380, 180), spaceAfter=64)
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 12),
        ]))
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkgrey, spaceBefore=1, spaceAfter=1, hAlign='CENTER', vAlign='BOTTOM', dash=None))
        elements.append(KeepTogether(table))
    document.build(elements)


@app.cli.command()
def create_proposals_document():
    """
    Create an Asciidoc document of all the proposals in the various sections.
    """
    file_path = str(file_directory.parent / 'proposals.adoc')
    total_proposals = len(Proposal.query.all())
    proposals_processed = 0
    with open(file_path, 'w') as proposals_file:
        proposals_file.write('= ACCUConf Proposals\n\n')

        def cleanup_text(text):
            text = text.replace('C++', '{cpp}')
            text = text.replace('====', '')
            text = re.sub('------*', '', text)
            return text

        def write_proposal(p):
            proposals_file.write('<<<\n\n=== {}\n\n'.format(p.title))
            proposals_file.write(', '.join('{} {}'.format(pp.first_name, pp.last_name) for pp in p.presenters) + '\n\n')
            proposals_file.write(cleanup_text(p.text.strip()) + '\n\n')
            scores = tuple(r.score for r in p.scores if r.score != 0)
            proposals_file.write("'''\n\n*{}{}*\n\n".format(', '.join(str(score.score) for score in p.scores), ' — {:.2f}, {}'.format(mean(scores), median(scores)) if len(scores) > 0 else ''))
            for comment in p.comments:
                c = comment.comment.strip()
                if c:
                    proposals_file.write("'''\n\n_{}_\n\n".format(comment.comment.strip()))
            nonlocal proposals_processed
            proposals_processed += 1

        proposals_file.write('== Full Day Workshops\n\n')
        for p in Proposal.query.filter_by(session_type='fulldayworkshop'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 90 minute presentations\n\n')
        for p in Proposal.query.filter_by(session_type='session'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 90 minute workshops\n\n')
        for p in Proposal.query.filter_by(session_type='miniworkshop'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 180 minute workshops\n\n')
        for p in Proposal.query.filter_by(session_type='workshop'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 15 minute presentations\n\n')
        for p in Proposal.query.filter_by(session_type='quickie'):
            write_proposal(p)

    if total_proposals != proposals_processed:
        print('###\n### Did not process all proposals, {} expected, dealt with {}.'.format(total_proposals, proposals_processed))
    else:
        print('Processed {} proposals.'.format(total_proposals))


@app.cli.command()
def check_database_consistency():
    """
    Make sure that all columns in all tables have the right sort of value.

    The tests for enum valued columns should never fail since the data
    schema contains the string constraints to ensure there is never a
    failure of the enum types.
    """
    #  May throw json.JSONDecodeError
    with open((file_directory.parent / 'accuconf' / 'static' / 'assets' / 'data' / 'countries.json').as_posix()) as countries_file:
        countries_data = json.load(countries_file)
    country_codes = tuple(c['alpha3'] for c in countries_data)

    def state_codes(country_code):
        country_data = tuple(c for c in countries_data if c['alpha3'] == country_code)
        assert len(country_data) == 1
        return tuple(r['code'] for r in country_data[0]['regions'])

    for u in User.query.all():
        if u.role not in Role:
            print('####  User {}, has role {}.'.format(u.email, u.role))
        if u.country not in country_codes:
            print('####  User {}, has country {}.'.format(u.email, u.country))
        else:
            if u.state not in state_codes(u.country):
                print('####  User {}, has state {}.'.format(u.email, u.state))

    for p in Proposal.query.all():
        if p.session_type not in SessionType:
            print('####  Proposal {} has sessiontype {}'.format(p.title, p.session_type))
        if p.audience not in SessionAudience:
            print('#### Proposal {} has audience {}'.format(p.title, p.audience))
        if p.category not in SessionCategory:
            print('#### Proposal {} has category {}'.format(p.title, p.category))
        if p.status not in ProposalState:
            print('#### Proposal {} has status {}'.format(p.title, p.status))
        if p.day is not None and p.day not in ConferenceDay:
            print('#### Proposal {} has day {}'.format(p.title, p.day))
        if p.session is not None and p.session not in SessionSlot:
            print('#### Proposal {} has session {}'.format(p.title, p.session))
        if p.quickie_slot is not None and p.quickie_slot not in QuickieSlot:
            print('#### Proposal {} has quickie_slot {}'.format(p.title, p.quickie_slot))
        if p.track is not None and p.track not in Track:
            print('#### Proposal {} has track {}'.format(p.title, p.track))
        if p.room is not None and p.room not in Room:
            print('#### Proposal {} has room {}'.format(p.title, p.room))

    for p in Presenter.query.all():
        if p.country not in country_codes:
            print('####  Presenter {}, has country {}.'.format(p.email, p.country))
        else:
            if p.state not in state_codes(p.country):
                print('####  Presenter {}, has state {}.'.format(p.email, p.state))


@app.cli.command()
def ensure_consistency_of_schedule():
    """
    Run a number of checks to ensure that the schedule has no obvious problems.
    """
    accepted = Proposal.query.filter_by(status=ProposalState.accepted).all()
    acknowledged = Proposal.query.filter_by(status=ProposalState.acknowledged).all()
    if len(accepted) > 0:
        print('####  There are accepted sessions that have not been acknowledged.')
        for a in accepted:
            print('\t' + a.title)
    accepted = accepted + acknowledged
    fulldayworkshops = Proposal.query.filter_by(day=ConferenceDay.workshops).all()
    incorrect = tuple(item for item in fulldayworkshops if item.session_type != SessionType.fulldayworkshop)
    if len(incorrect) > 0:
        print('####  There are scheduled full-day workshops that are not full-day workshops:')
        for item in incorrect:
            print('\t' + item.title)
    unacknowledged_workshops = tuple(w for w in fulldayworkshops if w not in acknowledged)
    if len(unacknowledged_workshops) > 0:
        print('####  The are full-day workshops accepted but not acknowledged.')
        for uw in unacknowledged_workshops:
            print('\t' + uw.title)
    keynotes = Proposal.query.filter_by(session_type=SessionType.keynote).all()
    if len(keynotes) != 4:
        print('####  Wrong number of keynotes')
    sessions = (
        Proposal.query.filter_by(day=ConferenceDay.day_1).all() +
        Proposal.query.filter_by(day=ConferenceDay.day_2).all() +
        Proposal.query.filter_by(day=ConferenceDay.day_3).all() +
        Proposal.query.filter_by(day=ConferenceDay.day_4).all()
    )
    if not all(s.status == ProposalState.acknowledged for s in sessions):
        print('####  There are unacknowledged scheduled sessions.')
    scheduled = fulldayworkshops + sessions
    if len(accepted) > len(scheduled):
        print('####  There are accepted sessions that are not scheduled.')
        for a in accepted:
            if a not in scheduled:
                print('\t' + a.title)
    elif len(accepted) < len(scheduled):
        print('####  There are schedule sessions that are not accepted.')
        for s in scheduled:
            if s not in accepted:
                print('\t' + s.title)
    for s in scheduled:
        lead_count = len(tuple(p for p in s.presenters if p.is_lead))
        if lead_count > 1:
            print('####  {} has multiple leads.'.format(s.title))
        elif lead_count == 0:
            print('####  {} has no lead.'.format(s.title))
    for day in ConferenceDay:
        if day == ConferenceDay.workshops:
            continue
        for session in SessionSlot:
            presenter_counter = Counter(p for s in sessions if s.day == day and s.session == session for p in s.presenters)
            for p in presenter_counter:
                if presenter_counter[p] > 1:
                    print('####  {} is presenting in two place in {}, {}'.format(p.email, day, session))
                elif presenter_counter[p] == 0:
                    print('####  Session {}, {} appears to have no presenters.'.format(day, session))
            for room in Room:
                if room == Room.bristol_suite:
                    continue
                sessions_now = tuple(s for s in sessions if s.day == day and s.session == session and s.room == room)
                if len(sessions_now) == 0:
                    print('####  {}, {}, {} appears empty'.format(day, session, room))
                elif len(sessions_now) > 1:
                    quickies = tuple(s for s in sessions_now if s.quickie_slot is not None)
                    if len(sessions_now) > len(quickies):
                        if len(quickies) > 0:
                            print('#### Quickies and non-quickies in same session')
                        print('#### Multiple sessions in {}, {}, {}:'.format(day, session, room))
                        for s in sessions_now:
                            print('\t' + ('(quickie) ' if s in quickies else '') + s.title)
                    else:
                        if len(quickies) != 4:
                            print('#### Too few quickies in {}, {}, {}'.format(day, session, room))
                else:
                    s = sessions_now[0]
                    if s.quickie_slot is not None:
                        print('####  Session listed as quickies scheduled as a session: {}, {}, {}, {}.'.format(s.title, day, session, room))
    presenter_counter = Counter(p for s in sessions if s.session_type != SessionType.quickie and s.session_type != SessionType.fulldayworkshop for p in s.presenters if p.is_lead)
    for p in presenter_counter:
        if presenter_counter[p] > 1:
            print('####  {} has more than one 90 minute session.'.format(p.email))
            for pp in (prop for prop in sessions if p in prop.presenters):
                print('\t' + pp.title)
        elif presenter_counter[p] == 0:
            print('#### #### This cannot be.')


@app.cli.command()
def list_of_unacknowledged():
    """
    List the sessions and emails of unacknowledged sessions.
    """
    proposals = Proposal.query.filter_by(status=ProposalState.accepted).all()
    quickies = tuple(p for p in proposals if p.session_type == SessionType.quickie)
    others = tuple(p for p in proposals if p.session_type != SessionType.quickie)
    assert set(proposals) == set(quickies) | set(others)
    for p in quickies:
        print('####  Quickie {} by {}, not yet acknowledged.'.format(p.title, p.proposer.email))
    for p in others:
        print('####  Session {} by {}, not yet acknowledged.'.format(p.title, p.proposer.email))


@app.cli.command()
def  list_of_lead_presenters():
    """
    List of people eligible for the presenter deal.
    """
    accepted = Proposal.query.filter_by(status=ProposalState.accepted).all()
    acknowledged = Proposal.query.filter_by(status=ProposalState.acknowledged).all()
    not_quickies = tuple(s for s in accepted + acknowledged if s.session_type != SessionType.quickie and s.session_type != SessionType.fulldayworkshop)
    for n_q in not_quickies:
        for p in tuple(p.presenter for p in n_q.presenters if p.is_lead):
            print("{} {}, {}".format(p.first_name, p.last_name, p.email))


@app.cli.command()
def generate_pages():
    """
    Generate the schedule, presenters, and sessions Asciidoc files for placing into the
    static part of the website.
    """
    accepted = Proposal.query.filter_by(status=ProposalState.accepted).all()
    assert len(accepted) == 0, 'There are unacknowledged accepted proposals.'
    acknowledged = Proposal.query.filter_by(status=ProposalState.acknowledged).all()
    presenters = set(p.presenter for s in acknowledged for p in s.presenters)
    for p in presenters:
        if p.bio.strip() == '':
            print('####  Presenter {}, has empty bio.'.format(p.email))
    workshops = set(item for item in acknowledged if item.day == ConferenceDay.workshops)
    assert all(item.session_type == SessionType.fulldayworkshop for item in workshops)
    sessions = set(item for item in acknowledged if item.day != ConferenceDay.workshops)
    day_names = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    room_names = ('Bristol 1', 'Bristol 2', 'Bristol 3', 'Empire', 'SS Great Britain')

    def valid_link(text):
        return ('X' + text
                .replace('+', '')
                .replace("'", '')
                .replace('-', '')
                .replace(':', '')
                .replace('.', '')
                .replace(' ', '')
                .replace('(', '')
                .replace(')', '')
                .replace('/', '')
                .replace(',', '')
                .replace('?', '')
                .replace('`', '')
                .replace('!', '')
                .replace('{', '')
                .replace('}', '')
        )

    def cppmark(text):
        return text.replace('C++', '{cpp}')

    def presenter_link(presenter):
        return 'link:presenters.html#{}[{}]'.format(
            valid_link(presenter.first_name + '_' + presenter.last_name),
            presenter.first_name + ' ' + presenter.last_name)

    def session_link(proposal):
        return 'link:sessions.html#{}[{}]'.format(valid_link(proposal.title), proposal.title)

    with open('sessions.adoc', 'w') as session_file:
        session_file.write('''
////
.. title: ACCU {} Sessions
.. description: List of session blurbs with links to presenters.
.. type: text
////
'''.format(start_date.year))
        for p in sorted(acknowledged, key=lambda x: x.title):
            presenter_links = ', '.join(presenter_link(pr) for pr in (pp.presenter for pp in sorted(p.presenters, key=lambda x: x.is_lead)))
            session_file.write('''
[[{}]]
== {}
=== {}

{}

'''.format(valid_link(p.title), cppmark(p.title), presenter_links, cppmark(p.text)))

    with open('presenters.adoc', 'w') as presenter_file:
        presenter_file.write('''
////
.. title: ACCU {} Presenters
.. description: List of presenter bios with links to session blurbs.
.. type: text
////
'''.format(start_date.year))
        for p in sorted(presenters, key=lambda x: x.first_name):
            proposals = tuple(pp.proposal for pp in p.proposals if pp.proposal.status == ProposalState.acknowledged)
            session_links = '\n\n'.join(session_link(pr) for pr in sorted(proposals, key=lambda x: x.title))
            presenter_file.write('''
[[{}]]
== {}

{}

{}

'''.format(valid_link(p.first_name + '_' + p.last_name), cppmark(p.first_name + ' ' + p.last_name), session_links, cppmark(p.bio)))

    with open('schedule.adoc', 'w') as schedule_file:
        schedule_file.write('''
////
.. title: ACCU {} Schedule
.. description: Schedule with links to session blurbs and presenter bios.
.. type: text
////

_The schedule is subject to change without notice until 2017-04-29._

'''.format(start_date.year))

        def heading(text):
            return '\n== {}\n\n'.format(text)

        def table(cols, *args):
            return '[cols="{}*^", options="header"]\n|===\n{}\n|===\n'.format(cols, '\n\n'.join(args))

        def row(*args):
            return '\n'.join(args)

        def banner(args):
            return tuple(single_column_entry('*{}*'.format(i)) for i in args)

        def first_column(name):
            return '|' + name

        def single_column_entry(*args):
            assert len(args) > 0
            return '|' + ' +\n'.join(str(item) for item in args)

        def all_columns_entry(cols, data):
            return '{}+^|'.format(cols) + data

        def all_columns_block(cols, data):
            return '{}+^'.format(cols) + data

        def session_and_presenters(proposal):
            #  TODO  Put the lead presenter first in the tuple.
            return (session_link(proposal), '', *tuple(presenter_link(p.presenter) for p in proposal.presenters))

        def schedule_write(text):
            schedule_file.write(text.replace('C++', '{cpp}'))

        workshop_data = tuple(single_column_entry(*session_and_presenters(item)) for item in workshops)
        schedule_write(
            heading(day_names[start_date.weekday()] + ' ' + start_date.isoformat()) +
            table(len(workshop_data) + 1,
                row(first_column(''), all_columns_entry(4, '')),
                row(first_column('10:00'), *workshop_data),
            )
        )

        def get_keynote(day):
            possibles = tuple(p for p in sessions if p.session_type == SessionType.keynote and p.day == day)
            assert len(possibles) == 1
            return possibles[0]

        def find_entry(day, session, room):
            ss = tuple(p for p in sessions if p.day == day and p.session == session and p.room == room)
            if len(ss) == 0:
                click.echo(click.style('Got no sessions for {}, {}, {}.'.format(day, session, room), fg='red'))
                return single_column_entry('TBC')
            elif len(ss) == 1:
                return single_column_entry(*session_and_presenters(ss[0]))
            elif len(ss) > 4:
                raise ValueError('Got {} sessions for {}, {}, {}.'.format(len(ss), day, session, room))
            else:
                assert all(p.quickie_slot is not None for p in ss)
                the_quickies = tuple(t for q in ss for t in session_and_presenters(q) + ('', ''))
                return single_column_entry(*the_quickies)

        def get_sessions(day, session):
            return (
                find_entry(day, session, Room.bristol_1),
                find_entry(day, session, Room.bristol_2),
                find_entry(day, session, Room.bristol_3),
                find_entry(day, session, Room.empire),
                find_entry(day, session, Room.great_britain),
            )

        def create_conference_day(i, id):
            d = start_date + timedelta(days=i)
            cols = len(room_names)
            schedule_write(
                heading(day_names[d.weekday()] + ' ' + d.isoformat()) +
                table(cols + 1,
                    row(first_column(''), *banner(room_names)),
                    row(first_column('09:30'), all_columns_block(cols, single_column_entry(*session_and_presenters(get_keynote(id))))),
                    row(first_column('10:30'), all_columns_entry(cols ,'Break')),
                    row(first_column('11:00'), *get_sessions(id, SessionSlot.session_1)),
                    row(first_column('12:30'), all_columns_entry(cols, 'Lunch')),
                    row(first_column('14:00'), *get_sessions(id, SessionSlot.session_2)),
                    row(first_column('15:30'), all_columns_entry(cols, 'Break')),
                    row(first_column('16:00'), *get_sessions(id, SessionSlot.session_3)),
                    row(first_column('17:30'), all_columns_entry(cols, 'Break')),
                    row(first_column('18:00'), all_columns_entry(cols, 'Lightning Talks')),
                    (
                        row(first_column('19:00'), all_columns_entry(cols, 'Welcome Reception')) if i == 1 else
                        row(first_column('19:00'), all_columns_entry(cols, 'Bloomberg ACCUChess17 (at Zerodegrees via coaches)')) if i == 2 else
                        row(first_column('19:30'), all_columns_entry(cols, 'Conference Supper')) if i == 3 else
                        ''
                    ),
                )
            )

        def create_conference_last_day(i, id):
            d = start_date + timedelta(days=i)
            cols = len(room_names)
            schedule_write(
                heading(day_names[d.weekday()] + ' ' + d.isoformat()) +
                table(cols + 1,
                    row(first_column(''), *banner(room_names)),
                    row(first_column('09:30'), *get_sessions(id, SessionSlot.session_1)),
                    row(first_column('11:00'), all_columns_entry(cols, 'Break')),
                    row(first_column('11:30'), *get_sessions(id, SessionSlot.session_2)),
                    row(first_column('13:00'), all_columns_entry(cols, 'Lunch')),
                    row(first_column('13:30'), all_columns_entry(cols, 'ACCU AGM')),
                    row(first_column(''), all_columns_entry(cols, '')),
                    row(first_column('14:30'), *get_sessions(id, SessionSlot.session_3)),
                    row(first_column('16:00'), all_columns_entry(cols, 'Break')),
                    row(first_column('16:30'), all_columns_block(cols, single_column_entry(*session_and_presenters(get_keynote(id))))),
                    row(first_column('17:30'), all_columns_entry(cols, 'Close')),
                )
            )

        create_conference_day(1, ConferenceDay.day_1)
        create_conference_day(2, ConferenceDay.day_2)
        create_conference_day(3, ConferenceDay.day_3)
        create_conference_last_day(4, ConferenceDay.day_4)


@app.cli.command()
def deploy_new_schedule_files():
    """
    Copy the three generated Asciidoc pages for the schedule, sessions,
    and presenters to their place in the static stories area.
    """
    destination = Path('..') / 'static_nikola_part' / 'stories' / str(start_date.year)
    for name in ('sessions.adoc', 'presenters.adoc', 'schedule.adoc'):
        shutil.copyfile(name, str(destination / name))


@app.cli.command()
@click.option('--trial/--not-trial', default=True)
@click.argument('emailout_spec')
def do_emailout(trial, emailout_spec):
    """
    Perform an emailout given data in the `emailout_spec`.
    The default is to run a trial emailout, the --trial|-t option must
    be explicitly set to False to do a real emailout.
    """
    emailout_directory = file_directory.parent / 'emailouts' / emailout_spec
    file_paths = tuple(emailout_directory / name for name in ('query.py', 'subject.txt', 'text.txt'))
    for fp in file_paths:
        if not Path(fp).exists():
            print('Cannot find required file {}'.format(fp))
            return 1
    old_path = sys.path
    sys.path.insert(0, emailout_directory.as_posix())
    import query
    del sys.path[0]
    assert sys.path == old_path
    with open(str(file_paths[1])) as subject_file:
        subject = subject_file.read().strip()
    with open(str(Path(os.environ['HOME']) / '.accuconf' / 'password')) as password_file:
        password = password_file.read().strip()

    def run_emailout():
        for proposal, person in query.query():
            if person is not None:
                email_address = (
                    '{} {} <russel@winder.org.uk>'.format(person.first_name, person.last_name) if trial else
                    '{} {} <{}>'.format(person.first_name, person.last_name, person.email)
                )
            else:
                print('####  No data of person to send email to.')
                return 1
            print('Subject:', subject)
            print('Recipient:', email_address)
            if proposal is not None:
                print('Title:', proposal.title)
            message = MIMEText(query.edit_template(str(file_paths[2]), proposal, person), _charset='utf-8')
            message['From'] = 'ACCUConf <conference@accu.org>'
            message['To'] = email_address
            message['Cc'] = 'ACCUConf <conference@accu.org>'
            message['Subject'] = subject
            message['Date'] = formatdate()  # RFC 2822 format.
            server.send_message(message)

    if trial:
        click.echo(click.style('Sending a test emailout via Winder server.', fg='green'))
        with SMTP('smtp.winder.org.uk') as server:
            run_emailout()
    else:
        click.echo(click.style('Sending a real emailout via ACCU server.', fg='yellow'))
        with SMTP('mail.accu.org') as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login('conference', password)
            run_emailout()


@app.cli.command()
@click.option('--selector', '-s', type=click.Choice(['bio', 'blurb']))
@click.argument('values', nargs=-1)
def edit(selector, values):
    """
    Edit either a bio (given an email) or a blurb (given a title) using the user's default editor.
    """
    if selector is None:
        click.echo(click.style('Must provide a --selector|-s option [bio|blurb]', fg='red'))
        return 1
    if len(values) == 0:
        click.echo(click.style('Processing all items is not yet supported, must provide argument(s).', fg='red'))
        return 1
    if selector == 'bio':
        value = values[0]
        presenters = Presenter.query.filter_by(email=value).all()
        if len(presenters) == 0:
            click.echo(click.style('Presenter with this email not found.', fg='red'))
        elif len(presenters) > 1:
            click.echo(click.style('Multiple presenters with this email found.', fg='red'))
        else:
            presenter = presenters[0]
            datum = click.edit(presenter.bio)
            if datum is not None and datum != presenter.bio:
                presenter.bio = datum
                db.session.commit()
                click.echo(click.style('Bio updated.', fg='green'))
            else:
                click.echo('Bio left unchanged.')
    elif selector == 'blurb':
        value = ' '.join(values)
        proposals = Proposal.query.filter_by(title=value).all()
        if len(proposals) == 0:
            click.echo(click.style('Proposal with this title not found.', fg='red'))
        elif len(proposals) > 1:
            click.echo(click.style('Multiple proposal with this title found.', fg='red'))
        else:
            proposal = proposals[0]
            datum = click.edit(proposal.text)
            if datum is not None and datum != proposal.title:
                proposal.text = datum
                db.session.commit()
                click.echo(click.style('Blurb updated.', fg='green'))
            else:
                click.echo('Blurb left unchanged.')
    else:
        click.echo(click.style('#### Panic now, this cannot happen', fg='red'))


@app.cli.command()
@click.argument('amendment_file_name')
def replace_proposal_abstract(amendment_file_name):
    """
    Read an amendment file and replace the proposal abstract specified with the given text.
    An amendment file comprises two sections separated by a line with just four dashes.
    The upper half is metadata specifying the proposer (email address) and title, the lower
    half is the text to replace what is currently in the database.
    """
    with open(amendment_file_name) as amendment_file:
        amendment_metadata, amendment_text = [x.strip() for x in amendment_file.read().split('----')]
        amendment_metadata = {k.strip(): v.strip() for k, v in [item.split(':') for item in amendment_metadata.splitlines()]}
        if 'Email' not in amendment_metadata or len(amendment_metadata['Email']) == 0:
            print('Email of proposer not specified.')
            return
        if 'Title' not in amendment_metadata or len(amendment_metadata['Title']) == 0:
            print('Title of proposal not specified.')
            return
        if len(amendment_text) == 0:
            print('Replacement text not specified')
            return
        proposals = Proposal.query.filter_by(proposer=amendment_metadata['Email'], title=amendment_metadata['Title']).all()
        if len(proposals) != 1:
            print('Query delivers no or more than one proposal object.')
            return
        proposals[0].text = amendment_text
        db.session.commit()
        print('Update apparently completed.')


@app.cli.command()
@click.argument('person')
def replace_presenter_of_proposal(person):
    """
    Replace the, or one of the, presenters associated with a proposal.

    The name is in the format <first_name>_<last_name> and refers to a directory
    in presenter_replacements directory. This directory must contain a file
    title.txt with the title of the proposal to be presented by the person being replaced.
    There must also be a file new_presenter.txt with details of the replacement presenter.
    This file must contain a line for each of the fields of a Presenter object:
    email, first_name, last_name, country, state, and then an Asciidoc paragraph for the bio.

    :param person: name of a directory in the presenter_replacements directory
    :return: None
    """
    directory = Path(__file__).parent.parent / 'presenter_replacements' / person
    if not directory.exists():
        print(person + ' replacement not set up correctly')
        return
    title_file = directory / 'title.txt'
    if not title_file.exists():
        print('no title.txt file for {} replacement'.format(person))
        return
    with open(str(title_file)) as f:
        title = f.read().strip()
    new_presenter_file = directory / 'new_presenter.txt'
    if not new_presenter_file.exists():
        print('no new_presenter.txt file for {} replacement'.format(person))
        return
    with open(str(new_presenter_file)) as f:
        email = f.readline().strip()
        first_name = f.readline().strip()
        last_name = f.readline().strip()
        country = f.readline().strip()
        state = f.readline().strip()
        bio = f.read().strip()
    proposal = Proposal.query.filter_by(title=title).all()
    if len(proposal) == 0:
        print('No proposal found with title: ' + title)
        return
    if len(proposal) > 1:
        print('Multiple proposals with the title: ' + title)
        return
    proposal = proposal[0]
    f_name, l_name = tuple(p.capitalize() for p in person.split('_'))
    old_presenter = Presenter.query.filter_by(first_name=f_name, last_name=l_name).all()
    if len(old_presenter) == 0:
        print('No presenter found with name: {} {}'.format(f_name, l_name))
        return
    if len(old_presenter) > 1:
        print('Multiple presenters found with name: {} {}'.format(f_name, l_name))
        return
    old_presenter = old_presenter[0]
    proposal_presenter = ProposalPresenter.query.filter_by(proposal=proposal, presenter=old_presenter).all()
    if len(proposal_presenter) == 0:
        print('No proposal_presenter found with title {}, and name {} {}'.format(proposal.title, old_presenter.first_name, old_presenter.last_name))
        return
    if len(proposal_presenter) > 1:
        print('Multiple proposal_presenters found with title {}, and name {} {}'.format(proposal.title, old_presenter.first_name, old_presenter.last_name))
        return
    proposal_presenter = proposal_presenter[0]
    new_presenter = Presenter(email, first_name, last_name, bio, country, state)
    print(proposal.title)
    print(old_presenter.email)
    print(new_presenter.email)
    print(proposal_presenter, proposal_presenter.proposal, proposal_presenter.presenter, proposal_presenter.is_lead)
    if old_presenter != proposal_presenter.presenter:
        print('Presenter not found, this cannot happen')
        return
    proposal_presenter.presenter = new_presenter
    print(proposal_presenter, proposal_presenter.proposal, proposal_presenter.presenter, proposal_presenter.is_lead)
    #db.session.commit()


@app.cli.command()
@click.argument('email_address')
def expunge_user(email_address):
    """
    Relationships have the wrong cascade settings and so we cannot just delete the user and have all
    the user related objects removed, we thus have to follow all the relationship entries in a class
    to perform a deep removal.

    User has user_info, location and proposals. user_info and location are simple things
    and can just be deleted. proposals is a list and each elements has presenters, status, scores,
    comments, category – only status is not a list.
    """
    user = User.query.filter_by(user_id=email_address).all()
    if len(user) == 0:
        print('Identifier {} not found.'.format(email_address))
        return
    elif len(user) > 1:
        print('Multiple instances of identifier {} found.'.format(email_address))
        return
    user = user[0]
    db.session.delete(user.user_info)
    db.session.delete(user.location)
    if user.proposals is not None:
        for proposal in user.proposals:
            if proposal.presenters is not None:
                for presenter in proposal.presenters:
                    db.session.delete(presenter)
            if proposal.status is not None:
                db.session.delete(proposal.status)
            if proposal.reviews is not None:
                for review in proposal.reviews:
                    db.session.delete(review)
            if proposal.comments is not None:
                for comment in proposal.comments:
                    db.session.delete(comment)
            if proposal.categories is not None:
                for category in proposal.categories:
                    db.session.delete(category)
            db.session.delete(proposal)
    db.session.delete(user)
    db.session.commit()
