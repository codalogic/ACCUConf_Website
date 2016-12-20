"""
This module provides all the additional CLI commands.
"""

import re
import sys

from collections import Counter
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
from accuconf.models import User, Proposal, Presenter, Score, Comment
from accuconf.proposals.utils.proposals import SessionType, ProposalState, SessionCategory, SessionAudience
from accuconf.proposals.utils.schedule import ConferenceDay, SessionSlot, QuickieSlot, Track, Room
from accuconf.proposals.utils.roles import Role


@app.cli.command()
def create_database():
    """Create an initial database."""
    db.create_all()


@app.cli.command()
def all_reviewers():
    """Print a list of all the registrants labelled as a scorer."""
    for x in User.query.filter_by(role=Role.reviewer).all():
        print('{} {} <{}>'.format(x.first_name, x.last_name, x.user_id))


@app.cli.command()
@click.argument('committee_email_file_path')
def committee_are_reviewers(committee_email_file_path):
    """Ensure consistency between committee list and scorer list."""
    try:
        with open(committee_email_file_path) as committee_email_file:
            committee_emails = {s.strip() for s in committee_email_file.read().split()}
            reviewer_emails = {u.user_id for u in User.query.filter_by(role=Role.reviewer).all()}
            committee_not_reviewer = {c for c in committee_emails if c not in reviewer_emails}
            reviewers_not_committee = {r for r in reviewer_emails if r not in committee_emails}
            print('Committee members not reviewers:', committee_not_reviewer)
            print('Reviewers not committee members:', reviewers_not_committee)
    except FileNotFoundError:
        print('{} not found..'.format(committee_email_file_path))


@app.cli.command()
def create_proposal_sheets():
    """Create the bits of papers for constructing an initial schedule."""
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
    """Create an Asciidoc document of all the proposals in the various sections."""
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
    workshops = Proposal.query.filter_by(day=ConferenceDay.workshops).all()
    unacknowledged_workshops = tuple(w for w in workshops if w not in acknowledged)
    if len(unacknowledged_workshops) > 0:
        print('####  The are full-day pre-conference workshops accepted but not acknowledged.')
        for uw in unacknowledged_workshops:
            print('\t' + uw.title)
    sessions = (
        Proposal.query.filter_by(day=ConferenceDay.day_1).all() +
        Proposal.query.filter_by(day=ConferenceDay.day_2).all() +
        Proposal.query.filter_by(day=ConferenceDay.day_3).all() +
        Proposal.query.filter_by(day=ConferenceDay.day_4).all()
    )
    scheduled = workshops + sessions
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
                    quickies = tuple(s for s in sessions_now if s.quickie_slot != None)
                    if len(sessions_now) != len(quickies):
                        print('####  Non-quickie scheduled in quickie session')
                        for s in sessions_now:
                            if s not in quickies:
                                print('\t' + s.title)
                    if len(quickies) != 4:
                        print('#### Too few quickies in {}, {}, {}'.format(day, session, room))

    presenter_counter = Counter(p for s in sessions if s.session_type != SessionType.quickie and s.session_type != SessionType.fulldayworkshop for p in s.presenters if p.is_lead)
    for p in presenter_counter:
        if presenter_counter[p] > 1:
            print('####  {} has more than one 90 minute session.'.format(p.email))
            for pp in (prop for prop in sessions if p in prop.presenters):
                print('\t' + pp.title)
        elif presenter_counter[p] == 0:
            print('#### #### This cannot be.')


@app.cli.command()
@click.argument('emailout_spec')
def do_emailout(emailout_spec):
    """
    Given an name of an emailout directory, which must contain query.py, subject.txt and text.txt files
    run a mailout. The query.py module must contain a query function that delivers a list of Proposal
    objects. The proposers of the proposals will be emailed. The query.py module must also contain a
    edit_template function that takes a path to a template file and a Proposal object and returns text
    that can be emailed. The subject.txt file must contain 1 short line of text that is the email subject.
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
    for proposal in query.query():
        email_address = '{} {} <{}>'.format(proposal.proposer.first_name, proposal.proposer.last_name, proposal.proposer.email)
        print('Subject:', subject)
        print('Recipient:', email_address)
        with SMTP('smtp.winder.org.uk') as server:
            message = MIMEText(query.edit_template(str(file_paths[2]), proposal), _charset='utf-8')
            message['From'] = 'conference@accu.org'
            message['To'] = email_address
            message['Cc'] = 'russel@winder.org.uk'
            message['Subject'] = subject
            message['Date'] = formatdate()  # RFC 2822 format.
            server.send_message(message)


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
