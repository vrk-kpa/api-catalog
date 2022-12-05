import pytest

import ckanext.apicatalog.db as apicatalog_model


@pytest.fixture
def apicatalog_setup():
    import ckan.model as model
    apicatalog_model.init_table(model.meta.engine)
