import ckanapi
import json
import argparse
import re
import string
import random
from ckan.lib import mailer

parser = argparse.ArgumentParser(description='Export users and their organizations')
parser.add_argument("BASE_URL", help="Base URL of ckan")
parser.add_argument("-a", "--apikey", help="Apikey")

args = parser.parse_args()

ckan = ckanapi.RemoteCKAN(args.BASE_URL, user_agent="user importer", apikey=args.apikey)

organizations = ckan.call_action('organization_list', requests_kwargs={'verify': False})

regex = re.compile(r'(-\d*$)')

def generate_password():
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(12))

with open("users.json", "r") as data:
    users = json.load(data)
    for user in users:
        username = re.sub(regex, '-test', user['name'])
        if user['name'] is username:
            username += "-test"
        if any(name in [org['name'] for org in user['organizations']] for name in organizations):
            print("Organization found, user should be created")
            try:
                user_obj = ckan.call_action('user_create', {"name": username, "email": user['email'],
                                             "password": generate_password() })
            except ckanapi.ValidationError as e:
                print("User already exists %s %s" % (username, e))
                user_obj = ckan.call_action('user_show', {"id": username})

            print("add user to organization")

            for org in user['organizations']:
                try:
                    ckan.call_action('organization_member_create', {'id': org['name'], 'username': user_obj['id'], 'role': org['capacity']})
                except ckanapi.ValidationError as e:
                    print("Organization not found %s" % org['name'])

            print("Send reset email")
            mailer.send_reset_link(user_obj)
