from ckan.plugins.toolkit import _


def facet_translations():
    return ["Subsystems with services", "Subsystems without services"]


def schema_translatable_strings():
    return [_('Same Organization Members'),
            _('Allowed Organizations Only'),
            _('Allowed Organizations'),
            _('Name in Finnish'),
            _('Name in Swedish'),
            _('Name in English'),
            _('Organisation description'),
            _('A general, concise, and easy-to-understand description of the organization'),
            _('Description in Finnish'),
            _('Description in Swedish'),
            _('Description in English'),
            _('Other information and settings'),
            _('Organisation logo'),
            _('The logo is displayed on the organization page in API Catalogue.'),
            _('If possible, provide a telephone number for the organization\'s switchboard or customer service, not an individual number.'),
            _('If possible, enter the email address of the organization or customer service, not the email address of the individual.'),
            _('Discard changes'),
            _('Save changes'),
            _('Write subsystem description'),
            ]
