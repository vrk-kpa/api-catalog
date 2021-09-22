from ckan.plugins.toolkit import _


def facet_translations():
    return ["Subsystems with services", "Subsystems without services"]


def schema_translatable_strings():
    return [_('Same Organization Members'),
            _('Allowed Organizations Only'),
            _('Allowed Organizations'),
            ]
