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
            _('If possible, provide a telephone number for the organization\'s switchboard or'
              ' customer service, not an individual number.'),
            _('If possible, enter the email address of the organization or customer service, '
              'not the email address of the individual.'),
            _('Email {email} is not a valid format'),
            _('Discard changes'),
            _('Save changes'),
            _('Write subsystem description'),
            _('Write attachment description'),
            _('Service name will be filled automatically and should not be edited'),
            _('Attachment name will be filled automatically and should not be edited'),
            _('Service visibility'),
            _('Service description'),
            _('Service name'),
            _('Attachment visibility'),
            _('Attachment description'),
            _('Attachment name'),
            _('When service visibility is private, it is only visible to the owner organisation or'
              ' users from allowed organisations'),
            _('When attachment visibility is private, it is only visible to the owner organisation or'
              ' users from allowed organisations'),
            _('Chargeable'),
            _('Free of charge'),
            _('Mentioned in service description'),
            _('No license specified'),
            _('Open Database license'),
            _('Web address'),
            _('URL will be formed automatically from the name of the application and should'
              ' in general not be edited.'),
            _('E-mail address in Finnish'),
            _('E-mail address in Swedish'),
            _('E-mail address in English'),
            _('Subsystem\'s title'),
            _('We recommend that the subsystem is given a clear name that describes its real name or purpose.'),
            _('The subsystem\'s name'),
            _('Title in Data Exchange Layer'),
            _('Subsystem description'),
            _('General, compact and easy to understand description of the subsystem. You can use markdown formatting '
              'in the description.<br><br><div class=\"collapsible-container\"><button type=\"button\" class=\"collapsible '
              'dataset-collapsible\" data-module=\"collapsible\">Instructions for writing the description '
              '<i class=\"collapsible-icon fa fa-chevron-down\"></i></button>'
              '<div class=\"collapsible-content dataset-collapsible-content\">'
              '<p>The description should contain at least the following things:</p>'
              '<ul><li>What services does the subsystem provide?<ul><li>'
              'What interfaces does the subsystem have?</li>'
              '<li>What kind of information can other organizations get through the services?</li></ul>'
              '<li>What kind of conditions and limitations have to be considered in the use of the subsystem\'s services?'
              '<ul><li>Is the use of the services, for example, limited to certain kinds of organizations?</li>'
              '<li>What\'s the cost of using the services?</li></ul></li><li>How can you get access to the service?'
              '<ul><li>What is the process like for the introduction of the service to use?</li>'
              '<li>Does the use of the service require, for example, acquiring an information permission?'
              '</li></ul></li></ul><p>More detailed instructions '
              'for writing the description of the service can be found in '
              '<a href=\"https://palveluhallinta.suomi.fi/en/tuki/artikkelit/5ef313c79a155e0139629cb5\">'
              'API catalog instructions</a>.</div></div>'),
            _('Write the subsystem\'s description'),
            _('Write the service\'s description'),
            _('Write the attachment\'s description'),
            _('Update Service'),
            _('Edit service'),
            _('Edit attachment'),
            _('Using keywords the user can easily find this application or similar applications through the search function. '
              'Choose at least one Finnish keyword.'),
            _('Write a keyword'),
            _('Maintainer\'s information'),
            _('Use the maintainer\'s common contact information.'),
            _('The name of the maintainer'),
            _('The email of the maintainer'),
            _('Limited'),
            _('Allowed organizations'),
            _('Other information'),
            _('dd/mm/yyyy'),
            _('fi'),
            _('en'),
            _('sv'),
            _('Organization acts as an intermediary for other organizations.'),
            _('Organization processes data outside the EU/EAA countries.'),
            _('Intermediary organization'),
            _('Data processing'),
            ]
