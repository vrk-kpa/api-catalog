import pytest
from ckan.plugins.toolkit import ValidationError
from ckan.tests.factories import User, Dataset, Organization, Resource
from ckan.tests.helpers import call_action
from .fixtures import apply_permissions_for_service_setup  # noqa

# import unittest.mock as mock
# from ckan import model

# from ckan.tests import factories
# import ckan.tests.helpers as helpers


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index', 'apply_permissions_for_service_setup')
@pytest.mark.ckan_config('ckan.plugins', 'apply_permissions_for_service apicatalog scheming_datasets scheming_organizations fluent markdown_editor')
class TestApplyPermissionsForServicePlugin():
    def test_user_creates_application(self):
        organization1 = Organization()

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]

        organization2 = Organization(id='TEST.ORG.1234567-1',
                                     users=org2_users,
                                     xroad_instance='TEST',
                                     xroad_memberclass='ORG',
                                     xroad_membercode='1234567-1')
        dataset1 = Dataset(owner_org=organization1['id'],
                           name='dataset1')
        resource1 = Resource(package_id=dataset1['id'],
                             xroad_servicecode='resource1',
                             xroad_serviceversion='v1')

        dataset2 = Dataset(owner_org=organization2['id'],
                           name='dataset2',
                           xroad_subsystemcode='dataset2')

        application = dict(
                    organization_id=organization2['id'],
                    target_organization_id=organization1['id'],
                    member_code=organization2['xroad_membercode'],
                    contact_name=user2['name'],
                    contact_email=user2['email'],
                    ip_address_list=['1.2.3.4'],
                    target_subsystem_id=dataset1['id'],
                    subsystem_id=dataset2['xroad_subsystemcode'],
                    service_id_list=[resource1['id']]
                    )
        call_action('service_permission_application_create',
                    {u"user": user2["name"], "ignore_auth": False},
                    **application
                    )

        applications = call_action('service_permission_application_list',
                                   {'user': user2['name'], 'ignore_auth': True})

        assert len(applications['sent']) == 1 and len(applications['received']) == 0
        for key, value in application.items():
            assert applications['sent'][0][key] == value

    def test_user_creates_application_with_inconsistent_subsystem(self):
        organization1 = Organization()

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]

        organization2 = Organization(id='TEST.ORG.1234567-1',
                                     users=org2_users,
                                     xroad_instance='TEST',
                                     xroad_memberclass='ORG',
                                     xroad_membercode='1234567-1')
        dataset1 = Dataset(owner_org=organization1['id'],
                           name='dataset1')
        resource1 = Resource(package_id=dataset1['id'],
                             xroad_servicecode='resource1',
                             xroad_serviceversion='v1')

        Dataset(owner_org=organization2['id'],
                name='dataset2',
                xroad_subsystemcode='dataset2')
        with pytest.raises(ValidationError):
            call_action('service_permission_application_create',
                        {u"user": user2["name"], "ignore_auth": False},
                        organization_id=organization2['id'],
                        target_organization_id=organization1['id'],
                        member_code=organization2['xroad_membercode'],
                        contact_name=user2['name'],
                        contact_email=user2['email'],
                        ip_address_list=['1.2.3.4'],
                        target_subsystem_id=dataset1['id'],
                        subsystem_id=dataset1['xroad_subsystemcode'],
                        service_id_list='.'.join([resource1['xroad_servicecode'],
                                                 resource1['xroad_serviceversion']])
                        )

        applications = call_action('service_permission_application_list',
                                   {'ignore_auth': True},
                                   target_subsystem_id=dataset1['id'])
        assert len(applications) == 0

    def test_user_creates_application_with_an_invalid_ip_list(self):
        organization1 = Organization()

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]

        organization2 = Organization(id='TEST.ORG.1234567-1',
                                     users=org2_users,
                                     xroad_instance='TEST',
                                     xroad_memberclass='ORG',
                                     xroad_membercode='1234567-1')
        dataset1 = Dataset(owner_org=organization1['id'],
                           name='dataset1')
        resource1 = Resource(package_id=dataset1['id'],
                             xroad_servicecode='resource1',
                             xroad_serviceversion='v1')

        dataset2 = Dataset(owner_org=organization2['id'],
                           name='dataset2',
                           xroad_subsystemcode='dataset2')

        application = dict(
                    organization_id=organization2['id'],
                    target_organization_id=organization1['id'],
                    member_code=organization2['xroad_membercode'],
                    contact_name=user2['name'],
                    contact_email=user2['email'],
                    ip_address_list=[''],
                    target_subsystem_id=dataset1['id'],
                    subsystem_id=dataset2['xroad_subsystemcode'],
                    service_id_list=[resource1['id']]
                    )

        with pytest.raises(ValidationError):
            call_action('service_permission_application_create',
                        {u"user": user2["name"], "ignore_auth": False},
                        **application
                        )

    def test_application_format(self):
        user1 = User()
        org1_users = [{"name": user1["name"], "capacity": "admin"}]
        target_organization = Organization(id='TEST.ORG.1234567-1',
                                           users=org1_users,
                                           xroad_instance='TEST',
                                           xroad_memberclass='ORG',
                                           xroad_membercode='1234567-1')

        target_subsystem = Dataset(owner_org=target_organization['id'],
                                   name='target_subsystem_name',
                                   id='TEST.ORG.1234567-1.target_subsystem_name')

        resource1 = Resource(package_id=target_subsystem['id'],
                             xroad_servicecode='service_name',
                             xroad_serviceversion='v1',
                             harvested_from_xroad=True)

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]
        organization = Organization(id='TEST.ORG.7654321-2',
                                    users=org2_users,
                                    xroad_instance='TEST',
                                    xroad_memberclass='ORG',
                                    xroad_membercode='7654321-2')

        subsystem = Dataset(owner_org=organization['id'],
                            name='subsystem_name',
                            xroad_subsystemcode='subsystem_name',
                            id='TEST.ORG.7654321-2.subsystem_name')

        application = dict(
                    organization_id=organization['id'],
                    member_code=organization['xroad_membercode'],
                    target_organization_id=target_organization['id'],
                    contact_name=user2['name'],
                    contact_email=user2['email'],
                    ip_address_list=['1.2.3.4'],
                    target_subsystem_id=target_subsystem['id'],
                    subsystem_id=subsystem['id'],
                    service_id_list=[resource1['id']]
                    )

        call_action('service_permission_application_create',
                    {u"user": user2["name"], "ignore_auth": False},
                    **application
                    )

        applications = call_action('service_permission_application_list',
                                   {'user': user2['name'], 'ignore_auth': True},
                                   target_subsystem_id=target_subsystem['id'])

        assert len(applications) == 1
        app = applications[0]
        assert app['organization_id'] == application['organization_id']
        assert app['target_organization_id'] == application['target_organization_id']
        assert app['member_code'] == application['member_code']
        assert app['contact_name'] == application['contact_name']
        assert app['contact_email'] == application['contact_email']
        assert app['ip_address_list'] == application['ip_address_list']
        assert app['target_subsystem_id'] == application['target_subsystem_id']
        assert app['subsystem_id'] == application['subsystem_id']
        assert app['service_id_list'] == application['service_id_list']
        assert app['target_subsystem']['id'] == application['target_subsystem_id']
        assert app['subsystem']['id'] == application['subsystem_id']
        assert app['services'][0]['id'] == resource1['id']
        assert app['organization']['id'] == application['organization_id']
        assert app['target_organization']['id'] == application['target_organization_id']

    def test_application_with_intermediate_organization(self, drop_db, migrate_db_for):

        migrate_db_for('apply_permissions_for_service')

        user1 = User()
        org1_users = [{"name": user1["name"], "capacity": "admin"}]
        target_organization = Organization(id='TEST.ORG.1234567-1',
                                           users=org1_users,
                                           xroad_instance='TEST',
                                           xroad_memberclass='ORG',
                                           xroad_membercode='1234567-1')

        target_subsystem = Dataset(owner_org=target_organization['id'],
                                   name='target_subsystem_name',
                                   id='TEST.ORG.1234567-1.target_subsystem_name')

        resource1 = Resource(package_id=target_subsystem['id'],
                             xroad_servicecode='service_name',
                             xroad_serviceversion='v1',
                             harvested_from_xroad=True)

        user2 = User()
        org2_users = [{"name": user2["name"], "capacity": "admin"}]
        organization = Organization(id='TEST.ORG.7654321-2',
                                    users=org2_users,
                                    xroad_instance='TEST',
                                    xroad_memberclass='ORG',
                                    xroad_membercode='7654321-2')

        subsystem = Dataset(owner_org=organization['id'],
                            name='subsystem_name',
                            xroad_subsystemcode='subsystem_name',
                            id='TEST.ORG.7654321-2.subsystem_name')

        user3 = User()
        org3_users = [{"name": user3["name"], "capacity": "admin"}]
        intermediate_organization = Organization(id='TEST.ORG.0123456-2',
                                                 users=org3_users,
                                                 xroad_instance='TEST',
                                                 xroad_memberclass='ORG',
                                                 xroad_membercode='0123456-2')

        application = dict(
                    organization_id=organization['id'],
                    member_code=organization['xroad_membercode'],
                    target_organization_id=target_organization['id'],
                    intermediate_organization_id=intermediate_organization['id'],
                    intermediate_member_code=intermediate_organization['xroad_membercode'],
                    contact_name=user2['name'],
                    contact_email=user2['email'],
                    ip_address_list=['1.2.3.4'],
                    target_subsystem_id=target_subsystem['id'],
                    subsystem_id=subsystem['id'],
                    service_id_list=[resource1['id']]
                    )

        call_action('service_permission_application_create',
                    {u"user": user3["name"], "ignore_auth": False},
                    **application)

        applications = call_action('service_permission_application_list',
                                   {'user': user3['name'], 'ignore_auth': True},
                                   target_subsystem_id=target_subsystem['id'])

        assert len(applications) == 1
        app = applications[0]
        assert app['organization_id'] == application['organization_id']
        assert app['target_organization_id'] == application['target_organization_id']
        assert app['intermediate_organization_id'] == application['intermediate_organization_id']
        assert app['member_code'] == application['member_code']
        assert app['intermediate_member_code'] == application['intermediate_member_code']
        assert app['subsystem_id'] == application['subsystem_id']
        assert app['subsystem']['id'] == application['subsystem_id']
        assert app['organization']['id'] == application['organization_id']
        assert app['target_organization']['id'] == application['target_organization_id']
        assert app['intermediate_organization']['id'] == application['intermediate_organization_id']
