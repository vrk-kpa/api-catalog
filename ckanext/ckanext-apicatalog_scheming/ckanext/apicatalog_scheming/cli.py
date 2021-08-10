import glob

import os
import sys

import click
import polib
import re
from ckanext.apicatalog_scheming.translations import facet_translations

from ckan.plugins.toolkit import get_action, config
from migrate import Migrate, plan_to_path
from migrations import migrations


def get_commands():
    return [apicatalog_translation, content]


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
            get_action('term_translation_update')({'ignore_auth': True}, {'term': term, 'term_translation': translation, 'lang_code': locale})


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
