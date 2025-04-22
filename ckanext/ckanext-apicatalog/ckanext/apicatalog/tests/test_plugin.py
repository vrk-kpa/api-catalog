import pytest
from ckan.tests.factories import User, Dataset, Organization, Resource
from ckan.plugins.toolkit import get_action, ObjectNotFound, NotAuthorized, ValidationError
from ckan.tests.helpers import call_action

import unittest.mock as mock
from ckan import model

from ckan.tests import factories
import ckan.tests.helpers as helpers

from .fixtures import apicatalog_setup  # noqa


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index', 'apicatalog_setup')
class TestApicatalogPlugin():
    def test_allowed_organization_user_should_see_subsystem(self):
        organization1 = Organization()

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]

        organization2 = Organization(users=org2_users)

        dataset = Dataset(private=True, owner_org=organization1['id'], allowed_organizations=organization2['name'])

        results = get_action(u"package_search")(
                {u"user": user2["name"]}, {u"include_private": True}
        )["results"]

        names = [r["name"] for r in results]
        assert names == [dataset['name']]

    def test_not_allowed_organization_user_should_not_see_subsystem(self):
        organization1 = Organization()

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]

        Organization(users=org2_users)

        Dataset(private=True, owner_org=organization1['id'], allowed_organizations="")

        results = get_action(u"package_search")(
            {u"user": user2["name"]}, {u"include_private": True}
        )["results"]

        names = [r["name"] for r in results]
        assert names == []

    def test_allowed_organization_user_should_see_service(self):
        organization1 = Organization()

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]

        organization2 = Organization(users=org2_users)

        dataset = Dataset(private=False, owner_org=organization1['id'])

        resource = Resource(package_id=dataset['id'], access_restriction_level="private",
                            allowed_organizations=organization2['name'])

        results = get_action(u"package_search")(
            {u"user": user2["name"]}, {})["results"]

        resources = [res['id'] for r in results for res in r.get('resources', [])]

        assert resources == [resource['id']]

        resource_show_results = get_action('resource_show')({u"user": user2["name"]}, {"id": resource['id']})

        assert resource_show_results['id'] == resource['id']

    def test_non_allowed_organization_user_should_not_see_service(self, app):
        organization1 = Organization()

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]

        Organization(users=org2_users)

        dataset = Dataset(private=False, owner_org=organization1['id'])

        resource = Resource(package_id=dataset['id'], access_restriction_level="private", allowed_organizations="")

        with app.flask_app.test_request_context():
            app.flask_app.preprocess_request()
            results = get_action(u"package_search")(
                {u"user": user2["name"], "ignore_auth": False}, {})["results"]

            resources = [res['id'] for r in results for res in r.get('resources', [])]

            assert resources == []

            with pytest.raises(ObjectNotFound):
                call_action('resource_show', {u"user": user2["name"], "ignore_auth": False}, id=resource['id'])

    @pytest.mark.usefixtures('with_request_context')
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

    @pytest.mark.usefixtures('with_request_context')
    def test_non_sysadmins_should_be_able_to_delete_attachments(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        subsystem = factories.Dataset(
            owner_org=org["id"]
        )

        service = factories.Resource(
            package_id=subsystem['id'],
        )

        context = {'ignore_auth': False, 'user': user['name']}

        helpers.call_action('resource_delete', context, id=service['id'])

    @pytest.mark.usefixtures('with_request_context')
    def test_non_sysadmins_should_not_be_able_to_delete_services(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        subsystem = factories.Dataset(
            owner_org=org["id"]
        )

        service = factories.Resource(
            package_id=subsystem['id'],
            harvested_from_xroad=True,
        )

        context = {'ignore_auth': False, 'user': user['name']}

        with pytest.raises(NotAuthorized):
            helpers.call_action('resource_delete', context, id=service['id'])

    @pytest.mark.usefixtures('with_request_context')
    def test_non_sysadmins_should_not_be_able_to_delete_organizations(self):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        context = {'ignore_auth': False, 'user': user['name']}

        with pytest.raises(NotAuthorized):
            helpers.call_action('organization_delete', context, id=org['id'])

    @pytest.mark.usefixtures('with_request_context')
    @mock.patch("ckan.lib.mailer.send_invite")
    def test_organization_admin_should_be_able_to_invite_user(self, _):
        user = factories.User()
        org_users = [{"name": user["name"], "capacity": "admin"}]
        org = factories.Organization(users=org_users)

        context = {"user": user["name"]}
        params = {"email": "foo@example.com", "group_id": org["id"], "role": "member"}

        result = helpers.call_action('user_invite', context, **params)

        assert model.User.get(result['id'])
        assert model.User.get(result['id']).is_pending()

        assert len(org['users']) == 2

    @pytest.mark.usefixtures('with_request_context')
    @mock.patch("ckan.lib.mailer.send_invite")
    def test_organization_admin_should_not_be_able_to_invite_user_to_other_organization(self, _):
        user = factories.User()

        other_organization = factories.Organization()

        context = {"user": user["name"], "ignore_auth": False}
        params = {"email": "foo@example.com", "group_id": other_organization["id"], "role": "member"}

        with pytest.raises(NotAuthorized):
            helpers.call_action('user_invite', context, **params)

    @pytest.mark.usefixtures('with_request_context')
    def test_inserting_resource_with_no_name_should_fail(self):
        subsystem = factories.Dataset()

        with pytest.raises(ValidationError):
            factories.Resource(package_id=subsystem['id'], name='')

    @mock.patch("ckan.lib.mailer.send_invite")
    @pytest.mark.usefixtures('with_request_context')
    def test_create_new_organization_user(self, _):
        org = factories.Organization(xroad_instance='TEST',
                                     xroad_memberclass='ORG',
                                     xroad_membercode='1234567-1')

        context = {"ignore_auth": True}
        helpers.call_action('create_user_to_organization', context,
                            fullname='New User',
                            email='test@example.com',
                            business_id=org['xroad_membercode'],
                            organization_name=org['name'])
        results = helpers.call_action('create_organization_users', context)['result']
        assert len(results['created']) == 1

    @mock.patch("ckan.lib.mailer.send_invite")
    @pytest.mark.usefixtures('with_request_context')
    def test_create_existing_organization_user(self, _):
        user = factories.User(email='existing@example.com')
        org = factories.Organization(xroad_instance='TEST',
                                     xroad_memberclass='ORG',
                                     xroad_membercode='1234567-1')

        context = {"ignore_auth": True}
        helpers.call_action('create_user_to_organization', context,
                            fullname=user['fullname'],
                            email=user['email'],
                            business_id=org['xroad_membercode'],
                            organization_name=org['name'])
        results = helpers.call_action('create_organization_users', context)['result']
        assert results['added'] == [user['name']]

    def test_old_business_ids_output_with_list(self):
        organization_with_python_list = Organization(old_business_ids=['1', '2'])

        assert organization_with_python_list['old_business_ids'] == ['1', '2']

    def test_user_should_not_see_subsystems_removed_from_xroad(self, app):
        org = factories.Organization()
        subsystem = factories.Dataset(
            owner_org=org["id"],
            xroad_removed=True
        )

        with app.flask_app.test_request_context():
            app.flask_app.preprocess_request()
            with pytest.raises(NotAuthorized):
                get_action('package_show')({}, {"id": subsystem['id']})

            search = get_action('package_search')({}, {})
            assert all(result['id'] != subsystem['id'] for result in search['results'])
