"""Tests for plugin.py."""
import pytest
import unittest.mock as mock
from ckan import model

from ckan.tests import factories
import ckan.tests.helpers as helpers
from ckan.plugins.toolkit import NotAuthorized


@pytest.mark.ckan_config('ckan.plugins', 'apicatalog_routes')
@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestApicatalogRoutes(object):

    def test_non_sysadmins_should_not_be_able_to_delete_subsystems(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        subsystem = factories.Dataset(
            owner_org=org["id"]
        )

        context = {'ignore_auth': False, 'user': user['name']}

        with pytest.raises(NotAuthorized):
            helpers.call_action('package_delete', context, id=subsystem['id'])

    def test_non_sysadmins_should_not_be_able_to_delete_services(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        subsystem = factories.Dataset(
            owner_org=org["id"]
        )

        service = factories.Resource(
            package_id=subsystem['id']
        )

        context = {'ignore_auth': False, 'user': user['name']}

        with pytest.raises(NotAuthorized):
            helpers.call_action('resource_delete', context, id=service['id'])

    def test_non_sysadmins_should_not_be_able_to_delete_organizations(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        context = {'ignore_auth': False, 'user': user['name']}

        with pytest.raises(NotAuthorized):
            helpers.call_action('organization_delete', context, id=org['id'])

    @mock.patch("ckan.lib.mailer.send_invite")
    def test_organization_admin_should_be_able_to_invite_user(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        context = {"user": user["name"]}
        params = {"email": "foo@example.com", "group_id": org["id"], "role": "member"}

        result = helpers.call_action('user_invite', context, **params)

        assert model.User.get(result['id'])
        assert model.User.get(result['id']).is_pending()

        assert len(org['users']) == 2

    @mock.patch("ckan.lib.mailer.send_invite")
    def test_organization_admin_should_not_be_able_to_invite_user_to_other_organization(self):
        user = factories.User()

        other_organization = factories.Organization()

        context = {"user": user["name"]}
        params = {"email": "foo@example.com", "group_id": other_organization["id"], "role": "member"}

        with pytest.raises(NotAuthorized):
            helpers.call_action('user_invite', context, **params)
