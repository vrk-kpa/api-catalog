import genson
import jsonschema
import requests

import argparse
import sys
import json
import csv
import smtplib
import datetime
from email.message import EmailMessage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('spec_file', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('validation_file', nargs='?', type=argparse.FileType('r'))
    parser.add_argument('--output', '-o', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--update', '-u', action='store_true')
    parser.add_argument('--include-samples', '-i', action='store_true')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--email-server')
    parser.add_argument('--email-from')
    parser.add_argument('--email-to')
    args = parser.parse_args()

    email_fields = [args.email_server, args.email_from, args.email_to]
    if any(email_fields) and not all(email_fields):
        print('Either provide all email parameters (server, from and to) or none of them')
        return

    spec = json.load(args.spec_file)
    validation = json.load(args.validation_file) if args.validation_file else {}
    valid = True
    output = []

    def log(msg):
        output.append(msg)
        print(msg)

    for item in spec.get('items'):
        name = item['name']

        # Merge optional profile and item into test config
        profile = spec.get('profiles', {}).get(item.get('profile'), {})
        config = profile.copy()
        config.update(item)

        try:
            response = make_request(spec, config)
        except Exception as e:
            log(f'{name} | {type(e).__name__}: {e}')
            valid = False
            continue

        validation_item = validation.get(name, {})
        validation_schema = validation_item.get('schema')

        if config['format'] == 'json':
            try:
                response = response.json()
            except requests.JSONDecodeError as e:
                log(f'{name} | {type(e).__name__}: {e}')
                valid = False
                continue

            builder = genson.SchemaBuilder()
            if validation_schema:
                builder.add_schema(validation_schema)

            if args.update:
                builder.add_object(response)
                validation[name] = {
                        'sample': response if args.include_samples else None,
                        'schema': builder.to_schema()
                        }
            else:
                schema = builder.to_schema()
                validator = jsonschema.Draft202012Validator(schema)
                item_valid = True
                for error in validator.iter_errors(response):
                    path = '.'.join(error.absolute_schema_path)
                    log(f'{name} | {path}: {error.message}')
                    valid = False
                    item_valid = False

                if not item_valid and args.verbose:
                    print('Received response')
                    print(response)
                    sample = validation_item.get('sample')
                    if sample:
                        print('It should look like:')
                        print(sample)

        elif config['format'] == 'csv':
            response = response.text
            first_line = next(csv.reader(response.splitlines()), None)
            if args.update:
                validation[name] = {
                        'sample': first_line,
                        'schema': first_line
                        }
            else:
                if first_line != validation_schema:
                    log(f'{name} | CSV header changed')
                    valid = False

                    if args.verbose:
                        print('Received response')
                        print(first_line)
                        sample = validation_item.get('sample')
                        if sample:
                            print('It should look like:')
                            print(sample)

    if output and all(email_fields):
        with smtplib.SMTP(args.email_server) as smtp:
            recipients = args.email_to.split(',')
            message = EmailMessage()
            message.add_header('From', args.email_from)
            message.add_header('To', ', '.join(recipients))
            message.add_header('Subject', f'api-verifier reported {len(output)} errors on {datetime.date.today()}')
            message.set_content('\n'.join(output))
            print(f'Sending output to {recipients} from {args.email_from} via {args.email_server}')
            try:
                smtp.send_message(message, args.email_from, recipients)
            except smtplib.SMTPException as e:
                print(f'Error sending message: {e}')
    if args.update and valid:
        json.dump(validation, args.output)
    elif not valid:
        sys.exit(1)


def make_request(spec, config):
    with requests.Session() as session:
        url = config.get('base_url', '') + config['url']
        variables = spec.get('variables', {})
        if variables:
            url = url.format(**variables)
        if 'cert' in config:
            cert = config['cert']
            if 'cert_password' in config:
                # Only require requests_pkcs12 if it is used
                from requests_pkcs12 import Pkcs12Adapter
                cert_password = config.get('cert_password')
                session.mount(url, Pkcs12Adapter(pkcs12_filename=cert, pkcs12_password=cert_password))
            else:
                session.cert = cert

        session.verify = config.get('cacert', session.verify)

        request = requests.Request(
                method=config.get('method', 'GET'),
                url=url,
                headers=config.get('headers'))

        return session.send(request.prepare())


if __name__ == '__main__':
    main()
