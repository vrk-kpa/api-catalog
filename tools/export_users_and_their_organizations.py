import ckanapi
import argparse
import json

parser = argparse.ArgumentParser(description='Export users and their organizations')
parser.add_argument("BASE_URL", help="Base URL of ckan")
parser.add_argument("-a", "--apikey", help="Apikey")

args = parser.parse_args()

ckan = ckanapi.RemoteCKAN(args.BASE_URL, user_agent="user exporter", apikey=args.apikey)

default_users = ['admin', 'default', 'harvest']

users = ckan.action.user_list()
users = [{'name': user.get('name'), 'email': user.get('email'), 'sysadmin': user.get('sysadmin')} for user in users if user.get('name') not in default_users]

for user in users:
    organizations = ckan.action.organization_list_for_user(id=user['name'])
    user['organizations'] = [{"name": organization.get('name'), "capacity": organization.get('capacity')} for organization in organizations]

with open("users.json", "w", encoding="utf-8") as f:
    json.dump(users, f, ensure_ascii=False, indent=4)