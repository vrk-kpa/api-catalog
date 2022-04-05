from typing import Any
from markupsafe import Markup
import ckan.plugins.toolkit as toolkit
_ = toolkit._


def custom_pager(page, *args: Any, **kwargs: Any) -> Markup:
    params = dict(
        link_attr={
            'aria-label': _('Go to page')
        },
    )
    params.update(kwargs)
    return page.pager(*args, **params)
