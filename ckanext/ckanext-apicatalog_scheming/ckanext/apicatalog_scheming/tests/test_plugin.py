import pytest
from ckan.tests.factories import User, Dataset, Organization
from ckan.plugins.toolkit import get_action


@pytest.mark.usefixtures('with_plugins', 'clean_db')
def test_allowed_organization_user_should_see_subsystem():
    organization1 = Organization()

    user2 = User()
    org2_users = [{"name": user2["name"], "capacity": "admin"}]

    organization2 = Organization(users=org2_users)

    Dataset(private=True, owner_org=organization1['id'], allowed_organizations=organization2['name'])

    results = get_action(u"package_search")(
            {u"user": user2["name"]}, {u"include_private": True}
    )["results"]

    names = [r["name"] for r in results]
    assert names == [u"d1"]
