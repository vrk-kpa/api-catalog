import glob

import os

import click
import polib
import re
from ckan.lib.cli import load_config, paster_click_group, click_config_option

from ckanext.apicatalog_scheming.translations import facet_translations

from ckan.plugins.toolkit import get_action

import logging
log = logging.getLogger(__name__)

apicatalog_translation_group = paster_click_group(
    summary=u'Translation commands for apicatalog'
)

@apicatalog_translation_group.command(
    u'add_facet_translations',
    help='Adds facet translations to database'
)

@click_config_option
@click.pass_context
@click.argument('i18n_root')
def add_facet_translation(ctx, config, i18n_root):
    load_config(config or ctx.obj['config'])

    terms = facet_translations()
    if len(terms) <= 0:
        print "No terms provided"
        return 1

    translated = []


    for locale, po_path in _get_po_files(i18n_root):
        found = 0
        for entry in polib.pofile(po_path):
            if entry.msgid in terms:
                translated.append((locale, entry.msgid, entry.msgstr))
                found += 1
        if found != len(terms):
            print "Term not found"
            return 1

    for term in terms:
        translated.append(('en', term, term))

    for locale, term, translation in translated:
        if translation:
            print(translated)
            get_action('term_translation_update')({'ignore_auth': True}, {'term': term, 'term_translation': translation, 'lang_code': locale})

def _get_po_files(path):
    pattern = re.compile('^[a-z]{2}(?:_[A-Z]{2})?$')

    for locale in os.listdir(path):
        if not pattern.match(locale):
            continue

        for po in glob.glob(os.path.join(path, locale, "LC_MESSAGES/*.po")):
            yield locale, po