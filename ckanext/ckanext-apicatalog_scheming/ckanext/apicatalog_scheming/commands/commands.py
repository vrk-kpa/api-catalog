from __future__ import absolute_import
import glob

import os

import click
import polib
import re
from ckanext.apicatalog_scheming.translations import facet_translations

from ckan.plugins.toolkit import get_action
from .migrate import content


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
