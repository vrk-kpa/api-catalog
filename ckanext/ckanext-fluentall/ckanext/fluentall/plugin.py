import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import pylons
import json
import pprint
import collections
import logging

# from ckanext.fluentall import validators
# from ckanext.fluentall.logic import (
#    fluentall_dataset_count, fluentall_dataset_terms_of_use,
#    fluentall_dataset_by_identifier
# )
# from ckanext.fluentall.helpers import (
#    get_dataset_count, get_group_count, get_app_count,
#    get_org_count, get_tweet_count, get_localized_value,
#    get_localized_org, get_localized_pkg, localize_json_title,
#    get_frequency_name, get_terms_of_use_icon, get_dataset_terms_of_use,
#    get_dataset_by_identifier, get_readable_file_size
# )
# 
log = logging.getLogger(__name__)
# 
LANGUAGES = ['en_GB', 'fi', 'sv']
# 
# 
# class FluentallPlugin(plugins.SingletonPlugin):
#     plugins.implements(plugins.IConfigurer)
#     plugins.implements(plugins.IValidators)
#     plugins.implements(plugins.IFacets)
#     plugins.implements(plugins.IActions)
#     plugins.implements(plugins.ITemplateHelpers)
# 
#     # IConfigurer
# 
#     def update_config(self, config_):
#         toolkit.add_template_directory(config_, 'templates')
#         toolkit.add_public_directory(config_, 'public')
#         toolkit.add_resource('fanstatic', 'fluentall')
# 
#     # IValidators
# 
#     def get_validators(self):
#         return {
#             'multiple_text': validators.multiple_text,
#             'multiple_text_output': validators.multiple_text_output,
#             'multilingual_text_output': validators.multilingual_text_output,
#             'list_of_dicts': validators.list_of_dicts,
#             'timestamp_to_datetime': validators.timestamp_to_datetime,
#             'fluentall_multiple_choice': validators.fluentall_multiple_choice,
#             'temporals_to_datetime_output': validators.temporals_to_datetime_output,
#             'parse_json': validators.parse_json,
#         }
# 
#     # IFacets
# 
#     def dataset_facets(self, facets_dict, package_type):
#         facets_dict = collections.OrderedDict()
#         facets_dict['groups'] = plugins.toolkit._('Themes')
#         facets_dict['tags'] = plugins.toolkit._('Keywords')
#         facets_dict['organization'] = plugins.toolkit._('Organization')
#         facets_dict['res_rights'] = plugins.toolkit._('Terms')
#         facets_dict['res_format'] = plugins.toolkit._('Media Type')
#         return facets_dict
# 
#     def group_facets(self, facets_dict, group_type, package_type):
#         facets_dict = collections.OrderedDict()
#         facets_dict['tags'] = plugins.toolkit._('Keywords')
#         facets_dict['organization'] = plugins.toolkit._('Organization')
#         facets_dict['res_rights'] = plugins.toolkit._('Terms')
#         facets_dict['res_format'] = plugins.toolkit._('Media Type')
#         return facets_dict
# 
#     def organization_facets(self, facets_dict, organization_type, package_type):
#         facets_dict = collections.OrderedDict()
#         facets_dict['groups'] = plugins.toolkit._('Themes')
#         facets_dict['tags'] = plugins.toolkit._('Keywords')
#         facets_dict['res_rights'] = plugins.toolkit._('Terms')
#         facets_dict['res_format'] = plugins.toolkit._('Media Type')
#         return facets_dict
# 
#     # IActions
# 
#     def get_actions(self):
#         """
#         Expose new API methods
#         """
#         return {
#             'fluentall_dataset_count': fluentall_dataset_count,
#             'fluentall_dataset_terms_of_use': fluentall_dataset_terms_of_use,
#             'fluentall_dataset_by_identifier': fluentall_dataset_by_identifier,
#         }
# 
#     # ITemplateHelpers
# 
#     def get_helpers(self):
#         """
#         Provide template helper functions
#         """
#         return {
#             'get_dataset_count': get_dataset_count,
#             'get_group_count': get_group_count,
#             'get_app_count': get_app_count,
#             'get_org_count': get_org_count,
#             'get_tweet_count': get_tweet_count,
#             'get_localized_org': get_localized_org,
#             'get_localized_pkg': get_localized_pkg,
#             'localize_json_title': localize_json_title,
#             'get_frequency_name': get_frequency_name,
#             'get_terms_of_use_icon': get_terms_of_use_icon,
#             'get_dataset_terms_of_use': get_dataset_terms_of_use,
#             'get_dataset_by_identifier': get_dataset_by_identifier,
#             'get_readable_file_size': get_readable_file_size,
#         }


class FluentallLanguagePlugin(plugins.SingletonPlugin):
    def _extract_lang_value(self, value, lang_code):
        log.warn("base extract_lang_value *********************************************************************")
        new_value = value
        try:
            if not isinstance(new_value, dict):
                new_value = json.loads(value)
        except (ValueError, TypeError, AttributeError):
            pass

        if not isinstance(new_value, dict):
            return value

        if lang_code in new_value:
            return new_value.get(lang_code)
        else:
            for c, v in new_value.iteritems():
                if lang_code.startswith(c):
                    return v
            return ''

    def before_view(self, pkg_dict):
        log.warn("base before_view *********************************************************************")
        try:
            desired_lang_code = pylons.request.environ['CKAN_LANG']
        except TypeError:
            desired_lang_code = pylons.config.get('ckan.locale_default', 'en')

        pkg_dict['display_name'] = pkg_dict['title']
        for key, value in pkg_dict.iteritems():
            if not self._ignore_field(key):
                pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)
        return pkg_dict

    def _ignore_field(self, key):
        return False


class FluentallGroupPlugin(FluentallLanguagePlugin):
    plugins.implements(plugins.IGroupController, inherit=True)

    # IGroupController
    def before_view(self, pkg_dict):
        return super(FluentallGroupPlugin, self).before_view(pkg_dict)


class FluentallOrganizationPlugin(FluentallLanguagePlugin):
    plugins.implements(plugins.IOrganizationController, inherit=True)

    # IOrganizationController

    def before_view(self, pkg_dict):
        return super(FluentallOrganizationPlugin, self).before_view(pkg_dict)


class FluentallResourcePlugin(FluentallLanguagePlugin):
    plugins.implements(plugins.IResourceController, inherit=True)

    # IResourceController

    def before_show(self, pkg_dict):
        return super(FluentallResourcePlugin, self).before_view(pkg_dict)

    def _ignore_field(self, key):
        return key == 'tracking_summary'


class FluentallPackagePlugin(FluentallLanguagePlugin):
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def before_view(self, pkg_dict):
        log.warn("before_view *********************************************************************")
        log.debug(pprint.pformat(pkg_dict))
        try:
            desired_lang_code = pylons.request.environ['CKAN_LANG']
        except TypeError:
            desired_lang_code = pylons.config.get('ckan.locale_default', 'en_GB')

        # pkg fields
        for key, value in pkg_dict.iteritems():
            pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)

        # groups
        for element in pkg_dict['groups']:
            for field in element:
                element[field] = self._extract_lang_value(element[field], desired_lang_code)

        # organization
        for field in pkg_dict['organization']:
            pkg_dict['organization'][field] = self._extract_lang_value(pkg_dict['organization'][field], desired_lang_code)

        # resources
        for resource in pkg_dict['resources']:
            if not resource['name'] and resource['title']:
                resource['name'] = resource['title']
            for key, value in resource.iteritems():
                if key not in ['tracking_summary']:
                    resource[key] = self._extract_lang_value(value, desired_lang_code)
        return pkg_dict

    def before_index(self, pkg_dict):
        log.debug("before_index *********************************************************************")
#        extract_title = LangToString('title')

#        log.debug(pprint.pformat(validated_dict))
#
#        pkg_dict['res_name'] = [r['title'] for r in validated_dict[u'resources']]
#        pkg_dict['res_format'] = [r['media_type'] for r in validated_dict[u'resources']]
#        pkg_dict['res_rights'] = [r['rights'] for r in validated_dict[u'resources']]
#        pkg_dict['title_string'] = extract_title(validated_dict)
#        pkg_dict['description'] = LangToString('description')(validated_dict)
#
#        for language in LANGUAGES:
#            pkg_dict['title_%s' % language] = validated_dict['title'][language]

        log.debug(pprint.pformat(pkg_dict))
        return pkg_dict

    def before_search(self, search_params):
        log.debug(pprint.pformat(search_params))
        return search_params


class LangToString(object):
    def __init__(self, attribute):
        self.attribute = attribute

    def __call__(self, data_dict):
        lang = data_dict[self.attribute]
        return " - ".join(lang[l] for l in LANGUAGES)
