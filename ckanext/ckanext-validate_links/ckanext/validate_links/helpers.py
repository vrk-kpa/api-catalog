from .model import LinkValidationResult
from datetime import datetime, timedelta


def organization_has_broken_links(organization_id):
    a_week_ago = datetime.today().date() - timedelta(weeks=1)
    results = LinkValidationResult.get_for_organization_since(organization_id, a_week_ago)
    return len(results) > 0
