import re
import sys

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# This must be imported here even though it may not be explicitly used in this file.
import click

file_directory = Path(__file__).absolute().parent
sys.path.insert(0, str(file_directory.parent))

from accuconf import app, db
from accuconf.models import User, UserInfo, UserLocation, Proposal, ProposalPresenter, ProposalReview, ProposalComment


@app.cli.command()
def create_database():
    """Create an initial database."""
    db.create_all()


@app.cli.command()
def all_reviewers():
    """Print a list of all the registrants labelled as a reviewer."""
    for x in UserInfo.query.filter_by(role='reviewer').all():
        print('{} {} <{}>'.format(x.first_name, x.last_name, x.user_id))


@app.cli.command()
def committee_are_reviewers():
    """Ensure consistency between committee list and reviewer list."""
    file_name = 'committee_emails.txt'
    try:
        with open(str(file_directory / file_name)) as committee_email_file:
            committee_emails = {s.strip() for s in committee_email_file.read().split()}
            reviewer_emails = {u.user_id for u in UserInfo.query.filter_by(role='reviewer').all()}
            committee_not_reviewer = {c for c in committee_emails if c not in reviewer_emails}
            reviewers_not_committee = {r for r in reviewer_emails if r not in committee_emails}
            print('Committee members not reviewers:', committee_not_reviewer)
            print('Reviewers not committee members:', reviewers_not_committee)
    except FileNotFoundError:
        print('{} not present in directory {}.'.format(file_name, file_directory))


@app.cli.command()
def create_proposal_sheets():
    """Create the bits of papers for constructing an initial schedule."""
    file_path = str(file_directory.parent / 'proposal_sheets.pdf')
    style_sheet = getSampleStyleSheet()['BodyText']
    style_sheet.fontSize = 18
    style_sheet.leading = 22
    document = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    for p in Proposal.query.all():
        table = Table([
            [Paragraph(p.title, style_sheet), p.session_type],
            [', '.join('{} {}'.format(pp.first_name, pp.last_name) for pp in p.presenters),
             ', '.join(str(r.score) for r in p.reviews)],
        ], colWidths=(400, 150), spaceAfter=36)
        table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)
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
            proposals_file.write("'''\n\n*{}*\n\n".format(', '.join(str(review.score) for review in p.reviews)))
            for comment in p.comments:
                c = comment.comment.strip()
                if c:
                    proposals_file.write("'''\n\n_{}_\n\n".format(comment.comment.strip()))
            nonlocal proposals_processed
            proposals_processed += 1

        proposals_file.write('== Full Day Workshops\n\n')
        for p in Proposal.query.filter_by(session_type='6 hour workshop'):
            write_proposal(p)
        for p in Proposal.query.filter_by(session_type='fulldayworkshop'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 90 minute presentations\n\n')
        for p in Proposal.query.filter_by(session_type='90 minutes, Interactive'):
            write_proposal(p)
        for p in Proposal.query.filter_by(session_type='interactive'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 90 minute workshops\n\n')
        for p in Proposal.query.filter_by(session_type='90 minutes, Mini Workshop'):
            write_proposal(p)
        for p in Proposal.query.filter_by(session_type='miniworkshop'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 180 minute workshops\n\n')
        for p in Proposal.query.filter_by(session_type='180 minutes, Workshop'):
            write_proposal(p)
        for p in Proposal.query.filter_by(session_type='workshop'):
            write_proposal(p)

        proposals_file.write('<<<\n\n== 15 minute presentations\n\n')
        for p in Proposal.query.filter_by(session_type='quick'):
            write_proposal(p)

    if total_proposals != proposals_processed:
        print('###\n### Did not process all proposals, {} expected, dealt with {}.'.format(total_proposals, proposals_processed))
    else:
        print('Processed {} proposals.'.format(total_proposals))


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