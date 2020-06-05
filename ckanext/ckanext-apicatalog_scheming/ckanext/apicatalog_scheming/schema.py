from ckan.logic.schema import validator_args

@validator_args
def create_user_to_organization_schema(not_empty, name_validator, user_name_validator, unicode_safe,
                                       email_validator, business_id_validator):
    return {
        "name": [not_empty, name_validator, user_name_validator, unicode_safe],
        "email": [not_empty, unicode_safe, email_validator],
        "business_id": [not_empty, unicode_safe, business_id_validator],
        "organization_name": [not_empty, unicode_safe]
    }

