from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from past.utils import old_div
import glob

import ckan.plugins.toolkit as t
import ckan.lib.mailer as mailer
from datetime import datetime


import os
import sys

import click
import polib
import re
from ckanext.apicatalog.translations import facet_translations

from ckan.plugins.toolkit import get_action, config
from .migrate import Migrate, plan_to_path
from .migrations import migrations


def get_commands():
    return [apicatalog_translation, content, apicatalog_admin, apicatalog_harvest, apicatalog_database]


@click.group()
def apicatalog_translation():
    'Translation commands for apicatalog'
    pass


@apicatalog_translation.command()
@click.pass_context
@click.argument('i18n_root')
def add_facet_translations(ctx, i18n_root):
    'Adds facet translations to database'
    terms = facet_translations()
    if len(terms) <= 0:
        click.echo("No terms provided")
        return 1

    translated = []

    for locale, po_path in _get_po_files(i18n_root):
        found = 0
        for entry in polib.pofile(po_path):
            if entry.msgid in terms:
                translated.append((locale, entry.msgid, entry.msgstr))
                found += 1
        if found != len(terms):
            click.echo("Term not found")
            return 1

    for term in terms:
        translated.append(('en', term, term))

    for locale, term, translation in translated:
        if translation:
            click.echo(translated)
            get_action('term_translation_update')({'ignore_auth': True},
                                                  {'term': term, 'term_translation': translation, 'lang_code': locale})


def _get_po_files(path):
    pattern = re.compile('^[a-z]{2}(?:_[A-Z]{2})?$')

    for locale in os.listdir(path):
        if not pattern.match(locale):
            continue

        for po in glob.glob(os.path.join(path, locale, "LC_MESSAGES/*.po")):
            yield locale, po


@click.group()
def content():
    'Content modification tools'
    pass


@content.command()
@click.argument('current_version')
@click.argument('target_version')
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--path-index', type=int)
@click.pass_context
def migrate(ctx, current_version, target_version, dryrun, path_index):
    'Migrates site content from one version to another'
    m = Migrate()

    for v1, v2, step in migrations():
        m.add(v1, v2, step)

    plans = m.plan(current_version, target_version)

    if not plans:
        click.echo('No migration paths found from {} to {}'.format(current_version, target_version))
        sys.exit(1)
    elif len(plans) > 1:
        if path_index is None:
            click.echo('Multiple migration paths found from {} to {}.'.format(current_version, target_version))
            click.echo('Run this command again with the option --path-index <your selection>')
            for i, plan in enumerate(plans):
                print('{}: {}'.format(i, ' -> '.join(plan_to_path(plan))))
            sys.exit(1)

        plan = plans[int(path_index)]
    else:
        plan = plans[0]

    click.echo('Using migration path: {}'.format(' -> '.join(plan_to_path(plan))))

    if dryrun:
        print('Performing a dry run')

    for v1, v2, step in plan:
        print('Migrating from {} to {}'.format(v1, v2))
        step(ctx, config, dryrun)

    click.echo('Finished migration successfully')


@click.group()
def apicatalog_admin():
    '''Creates users based on records uploaded to create_user_to_organization endpoint'''
    pass


@apicatalog_admin.command(
    u'create-organization-users',
    help='Creates users based on records uploaded to create_user_to_organization endpoint'
)
@click.pass_context
@click.option(u'--retry', is_flag=True)
def create_organization_users(ctx, retry):

    site_user = t.get_action('get_site_user')({'ignore_auth': True})

    flask_app = ctx.meta["flask_app"]
    with flask_app.test_request_context():
        result = t.get_action('create_organization_users')({'ignore_auth': True, 'user': site_user['name']},
                                                           {'retry': retry}).get('result', {})

    created = result.get('created', [])
    invalid = result.get('invalid', [])
    ambiguous = result.get('ambiguous', [])
    duplicate = result.get('duplicate', [])
    click.echo('Created users: %s' % ', '.join(created))
    click.echo('Duplicate users: %s' % ', '.join(duplicate))
    click.echo('Unknown business ids: %s' % ', '.join(invalid))
    click.echo('Ambiguous business ids: %s' % ', '.join(ambiguous))


@click.group()
def apicatalog_harvest():
    '''Harvester related commands.'''
    pass


@apicatalog_harvest.command(
    u'send-status-emails',
    help='Sends harvester status emails to configured recipients'
)
@click.pass_context
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--force', is_flag=True)
@click.option(u'--all-harvesters', is_flag=True)
def send_harvester_status_emails(ctx, dryrun, force, all_harvesters):
    email_notification_recipients = t.aslist(t.config.get('ckanext.apicatalog.harvester_status_recipients', ''))

    if not email_notification_recipients and not dryrun:
        click.echo('No recipients configured')
        return

    status_opts = {} if not all_harvesters else {'include_manual': True, 'include_never_run': True}
    status = t.get_action('harvester_status')({}, status_opts)

    errored_runs = any(item.get('errors') != 0 for item in status.values())
    running = [item.get('started') for item in status.values() if item.get('status') == 'running']
    stuck_runs = any(_elapsed_since(started).days >= 1 for started in running)

    if not (errored_runs or stuck_runs) and not force:
        click.echo('Nothing to report')
        return

    if len(status) == 0:
        click.echo('No harvesters matching criteria found')
        return

    site_title = t.config.get('ckan.site_title', '')
    today = datetime.now().date().isoformat()

    status_templates = {
        'running': '%%(title)-%ds | Running since %%(time)s with %%(errors)d errors',
        'finished': '%%(title)-%ds | Finished %%(time)s with %%(errors)d errors',
        'pending': '%%(title)-%ds | Pending since %%(time)s'}
    unknown_status_template = '%%(title)-%ds | Unknown status: %%(status)s'
    max_title_length = max(len(title) for title in status)

    def status_string(title, values):
        template = status_templates.get(values.get('status'), unknown_status_template)
        status = values.get('status')
        time_field = 'finished' if status == 'finished' else 'started'
        return template % max_title_length % {
            'title': title,
            'time': _pretty_time(values.get(time_field)),
            'status': status,
            'errors': values.get('errors')
        }

    msg = '%(site_title)s - Harvester summary %(today)s\n\n%(status)s' % {
        'site_title': site_title,
        'today': today,
        'status': '\n'.join(status_string(title, values) for title, values in list(status.items()))
    }

    subject = '%s - Harvester summary %s' % (site_title, today)
    _send_harvester_notification(subject, msg, email_notification_recipients, dryrun)

    if dryrun:
        click.echo(msg)


@apicatalog_harvest.command(
    u'send-stuck-runs-report',
    help='Sends stuck runs report to configured recipients'
)
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--force', is_flag=True)
@click.option(u'--all-harvesters', is_flag=True)
@click.pass_context
def send_stuck_runs_report(ctx, dryrun, force, all_harvesters):
    email_notification_recipients = t.aslist(t.config.get('ckanext.apicatalog.fault_recipients', ''))

    if not email_notification_recipients and not dryrun:
        click.echo('No recipients configured')
        return

    status_opts = {} if not all_harvesters else {'include_manual': True, 'include_never_run': True}
    status = t.get_action('harvester_status')({}, status_opts)

    stuck_runs = [(title, job_status) for title, job_status in status.items()
                  if job_status.get('status') == 'running' and _elapsed_since(job_status.get('started')).days >= 1]

    if stuck_runs:
        site_title = t.config.get('ckan.site_title', '')

        msg = '%(site_title)s - Following harvesters have been running more than 24 hours: \n\n%(status)s\n\n' \
              'Instructions to fix this can be found from here %(instructions)s' % \
              {
                  'site_title': site_title,
                  'status': '\n'.join('%s has been stuck since %s' %
                                      (title, status.get('started')) for title, status in stuck_runs),
                  'instructions': t.config.get('ckanext.apicatalog.harvester_instruction_url', 'url not configured')
              }

        subject = '%s - There are stuck harvester runs that need to have a look at' % site_title
        _send_harvester_notification(subject, msg, email_notification_recipients, dryrun)

        if dryrun:
            click.echo(msg)
    else:
        click.echo('Nothing to report')


def _send_harvester_notification(subject, msg, recipients, dryrun):

    for recipient in recipients:
        email = {'recipient_name': recipient,
                 'recipient_email': recipient,
                 'subject': subject,
                 'body': msg}

        if dryrun:
            click.echo('to: %s' % recipient)
        else:
            try:
                mailer.mail_recipient(**email)
            except mailer.MailerException as e:
                click.echo('Sending harvester notification to %s failed: %s' % (recipient, e))


def _elapsed_since(t):
    if t is None:
        return t
    if isinstance(t, str):
        t = datetime.strptime(t, '%Y-%m-%d %H:%M:%S.%f')
    return datetime.now() - t


def _pretty_time(t):
    if t is None:
        return 'unknown'

    delta = _elapsed_since(t)
    if delta.days == 0:
        return 'today'
    if delta.days == 1:
        return 'yesterday'
    elif delta.days < 30:
        return '%d days ago' % delta.days
    elif delta.days < 365:
        return '%d months ago' % int(old_div(delta.days, 30))
    else:
        return '%d years ago' % int(old_div(delta.days, 365))


@click.group()
def apicatalog_database():
    '''Database commands for apicatalog.'''


@apicatalog_database.command()
@click.pass_context
def init(ctx):
    'Initializes database for apicatalog'
    import ckan.model as model
    from .db import init_table
    init_table(model.meta.engine)
