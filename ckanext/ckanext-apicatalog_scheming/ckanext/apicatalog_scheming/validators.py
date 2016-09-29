from ckan.common import _
import ckan.lib.navl.dictization_functions as df


def lower_if_exists(s):
    return s.lower() if s else s


def upper_if_exists(s):
    return s.upper() if s else s


def valid_resources(x, context):
    package = context.get('package')
    if package and not package.private:
        for resource in package.resources:
            if resource.extras.get('valid_content') == 'no':
                raise df.Invalid(_("Package contains invalid resources"))
    return x
