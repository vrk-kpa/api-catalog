import pytest

import ckanext.apply_permissions_for_service.model as apply_permissions_for_service_model
from ckan import model


@pytest.fixture
def apply_permissions_for_service_setup():
    import ckan.model as model
    apply_permissions_for_service_model.init_table(model.meta.engine)


@pytest.fixture
def drop_db():
    model.Session.close_all()

    model.repo.clean_db()
    model.repo.init_db()
