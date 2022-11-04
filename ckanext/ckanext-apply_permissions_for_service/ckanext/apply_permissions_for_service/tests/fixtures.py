import pytest

import ckanext.apply_permissions_for_service.model as apply_permissions_for_service_model


@pytest.fixture
def apply_permissions_for_service_setup():
    import ckan.model as model
    apply_permissions_for_service_model.init_table(model.meta.engine)
