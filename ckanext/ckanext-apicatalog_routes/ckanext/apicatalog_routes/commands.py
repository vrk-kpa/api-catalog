# -*- coding: utf8 -*-

from ckan.lib.cli import CkanCommand
from ckan.logic import get_action, ValidationError
import ckan.plugins.toolkit as t
import ckan.lib.mailer as mailer
from datetime import datetime

from ckan.plugins.toolkit import config as c

import click

from ckan.lib.cli import (
    load_config,
    paster_click_group,
    click_config_option,
)


import itertools

apicatalog_harvest_group = paster_click_group(
    summary=u'Harvester related commands.'
)


@apicatalog_harvest_group.command(
    u'send-status-emails',
    help='Sends harvester status emails to configured recipients'
)
@click_config_option
@click.option(u'--dryrun', is_flag=True)
@click.option(u'--force', is_flag=True)
@click.option(u'--all-harvesters', is_flag=True)
@click.pass_context
def send_harvester_status_emails(ctx, config, dryrun, force, all_harvesters):
    load_config(config or ctx.obj['config'])

    email_notification_recipients = t.aslist(t.config.get('ckanext.apicatalog.harvester_status_recipients', ''))

    if not email_notification_recipients and not dryrun:
        print 'No recipients configured'
        return

    status_opts = {} if not all_harvesters else {'include_manual': True, 'include_never_run': True}
    status = get_action('harvester_status')({}, status_opts)

    errored_runs = any(item.get('errors') != 0 for item in status.values())
    running = (item.get('started') for item in status.values() if item.get('status') == 'running')
    stuck_runs = any(_elapsed_since(started).days > 1 for started in running)

    if not (errored_runs or stuck_runs) and not force:
        print 'Nothing to report'
        return

    if len(status) == 0:
        print 'No harvesters matching criteria found'
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
            'status': '\n'.join(status_string(title, values) for title, values in status.items())
            }

    for recipient in email_notification_recipients:
        email = {'recipient_name': '',
                 'recipient_email': recipient,
                 'subject': '%s - Harvester summary %s' % (site_title, today),
                 'body': msg}

        if dryrun:
            print 'to: %s' % recipient
        else:
            try:
                mailer.mail_recipient(**email)
            except mailer.MailerException as e:
                print 'Sending harvester summary to %s failed: %s' % (recipient, e)

    if dryrun:
        print msg


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
        return '%d months ago' % int(delta.days / 30)
    else:
        return '%d years ago' % int(delta.days / 365)


apicatalog_database_group = paster_click_group(
    summary=u'Database commands for apicatalog.'
)


@apicatalog_database_group.command(
    u'init',
    help='Initializes database for apicatalog'
)

@click_config_option
@click.pass_context
def init(ctx, config):
    load_config(config or ctx.obj['config'])
    import ckan.model as model
    from db import init_table
    init_table(model.meta.engine)