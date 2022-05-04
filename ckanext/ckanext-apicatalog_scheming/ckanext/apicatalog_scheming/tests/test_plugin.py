import pytest
from ckan.tests.factories import User, Dataset, Organization, Resource
from ckan.plugins.toolkit import get_action, ObjectNotFound
from ckan.tests.helpers import call_action


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
def test_allowed_organization_user_should_see_subsystem():
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


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
def test_not_allowed_organization_user_should_not_see_subsystem():
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


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
def test_allowed_organization_user_should_see_service():
    organization1 = Organization()

    user2 = User()
    org2_users = [{"name": user2["name"], "capacity": "admin"}]

    organization2 = Organization(users=org2_users)

    dataset = Dataset(title_translated={"fi": "finnish title"}, keywords={"fi": ["some keyword"]},
                      private=False, owner_org=organization1['id'])

    resource = Resource(package_id=dataset['id'], access_restriction_level="private",
                        allowed_organizations=organization2['name'])

    results = get_action(u"package_search")(
        {u"user": user2["name"]}, {})["results"]

    resources = [res['id'] for r in results for res in r.get('resources', [])]

    assert resources == [resource['id']]

    resource_show_results = get_action('resource_show')({u"user": user2["name"]}, {"id": resource['id']})

    assert resource_show_results['id'] == resource['id']


@pytest.mark.usefixtures('with_plugins', 'clean_db', 'clean_index')
def test_non_allowed_organization_user_should_not_see_service(app):
    organization1 = Organization()

    user2 = User()
    org2_users = [{"name": user2["name"], "capacity": "admin"}]

    Organization(users=org2_users)

    dataset = Dataset(title_translated={"fi": "finnish title"}, keywords={"fi": ["some keyword"]},
                      private=False, owner_org=organization1['id'])

    resource = Resource(package_id=dataset['id'], access_restriction_level="private", allowed_organizations="")

    with app.flask_app.test_request_context():
        app.flask_app.preprocess_request()
        results = get_action(u"package_search")(
            {u"user": user2["name"], "ignore_auth": False}, {})["results"]

        resources = [res['id'] for r in results for res in r.get('resources', [])]

        assert resources == []

        with pytest.raises(ObjectNotFound):
            call_action('resource_show', {u"user": user2["name"], "ignore_auth": False}, id=resource['id'])
