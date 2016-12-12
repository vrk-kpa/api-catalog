from ckan.common import _
import ckan.lib.navl.dictization_functions as df


def lower_if_exists(s):
    return s.lower() if s else s


def upper_if_exists(s):
    return s.upper() if s else s


def valid_resources(private, context):
    package = context.get('package')
    if not package:
        return private

    change = package.get('private') != private
    to_public = private is False or private == u'False'

    if change and to_public:
        for resource in package.resources:
            if resource.extras.get('valid_content') == 'no':
                raise df.Invalid(_("Package contains invalid resources"))
    return private
