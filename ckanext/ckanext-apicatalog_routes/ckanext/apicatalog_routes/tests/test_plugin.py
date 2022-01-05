"""Tests for plugin.py."""
import pytest

from ckan.tests import factories
import ckan.tests.helpers as helpers
from ckan.plugins.toolkit import NotAuthorized

@pytest.mark.ckan_config('ckan.plugins', 'apicatalog_routes')
@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class ApicatalogRoutesTests(object):

    def test_non_sysadmins_should_not_be_able_to_delete_subsystems(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        subsystem = factories.Dataset(
            owner_org=org["id"]
        )

        context = {'ignore_auth': False, 'user': user['name']}

        with pytest.raises(NotAuthorized):
            helpers.call_action('package_delete', context, name=subsystem['name'])

