import ckan.plugins as plugins
import pylons
import json
import logging

log = logging.getLogger(__name__)
LANGUAGES = ['en_GB', 'fi', 'sv']


class FluentallLanguagePlugin(plugins.SingletonPlugin):
    def _extract_lang_value(self, value, lang_code):
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
        try:
            desired_lang_code = pylons.request.environ['CKAN_LANG']
        except TypeError:
            desired_lang_code = pylons.config.get('ckan.locale_default', 'en')

        pkg_dict['display_name'] = pkg_dict.get('title', '')
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

    def before_view(self, pkg_dict):
        return super(FluentallResourcePlugin, self).before_view(pkg_dict)

    def _ignore_field(self, key):
        return key == 'tracking_summary'


class FluentallPackagePlugin(FluentallLanguagePlugin):
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def before_view(self, pkg_dict):
        try:
            desired_lang_code = pylons.request.environ['CKAN_LANG']
        except TypeError:
            desired_lang_code = pylons.config.get('ckan.locale_default', 'en_GB')

        # pkg fields
        for key, value in pkg_dict.iteritems():
            pkg_dict[key] = self._extract_lang_value(value, desired_lang_code)

        # groups
        for element in pkg_dict.get('groups', []):
            for field in element:
                element[field] = self._extract_lang_value(element[field], desired_lang_code)

        # organization
        for field in pkg_dict['organization']:
            pkg_dict['organization'][field] = self._extract_lang_value(pkg_dict['organization'][field], desired_lang_code)

        # resources
        for resource in pkg_dict.get('resources', []):
            if not resource.get('name', '') and resource.get('title', ''):
                resource['name'] = resource.get('title', '')
            for key, value in resource.iteritems():
                if key not in ['tracking_summary']:
                    resource[key] = self._extract_lang_value(value, desired_lang_code)
        return pkg_dict

    def before_index(self, pkg_dict):
        return pkg_dict

    def before_search(self, search_params):
        return search_params


class LangToString(object):
    def __init__(self, attribute):
        self.attribute = attribute

    def __call__(self, data_dict):
        lang = data_dict[self.attribute]
        return " - ".join(lang[l] for l in LANGUAGES)
