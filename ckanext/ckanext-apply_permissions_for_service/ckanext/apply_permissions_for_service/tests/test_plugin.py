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
                    business_code=organization2['xroad_membercode'],
                    contact_name=user2['name'],
                    contact_email=user2['email'],
                    ip_address_list=['1.2.3.4'],
                    subsystem_id=dataset1['id'],
                    subsystem_code=dataset2['xroad_subsystemcode'],
                    service_code_list=[resource1['id']]
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
                        business_code=organization2['xroad_membercode'],
                        contact_name=user2['name'],
                        contact_email=user2['email'],
                        ip_address_list=['1.2.3.4'],
                        subsystem_id=dataset1['id'],
                        subsystem_code=dataset1['xroad_subsystemcode'],
                        service_code_list='.'.join([resource1['xroad_servicecode'],
                                                    resource1['xroad_serviceversion']])
                        )

        applications = call_action('service_permission_application_list',
                                   {'ignore_auth': True},
                                   subsystem_id=dataset1['id'])
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
                    business_code=organization2['xroad_membercode'],
                    contact_name=user2['name'],
                    contact_email=user2['email'],
                    ip_address_list=[''],
                    subsystem_id=dataset1['id'],
                    subsystem_code=dataset2['xroad_subsystemcode'],
                    service_code_list=[resource1['id']]
                    )

        with pytest.raises(ValidationError):
            call_action('service_permission_application_create',
                        {u"user": user2["name"], "ignore_auth": False},
                        **application
                        )
