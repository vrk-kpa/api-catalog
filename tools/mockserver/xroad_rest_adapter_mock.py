from flask import Flask, send_file, jsonify, request
import json

DATA = json.load(open('listMembers.json', 'r'))

app = Flask(__name__)


@app.route('/rest-adapter-service/Consumer/ListMembers')
def list_members():
    return send_file('listMembers.json')


@app.route('/rest-adapter-service/Consumer/IsProvider')
def is_provider():
    xroad_instance = request.args.get('xRoadInstance')
    member_class = request.args.get('memberClass')
    member_code = request.args.get('memberCode')
    member = find_member(DATA, xroad_instance, member_class, member_code)
    subsystem_count = len(xroad_list_to_list(member, 'subsystems', 'subsystem'))
    return jsonify({'provider': subsystem_count > 0})


@app.route('/rest-adapter-service/Consumer/GetWsdl')
def get_wsdl():
    return jsonify({'wsdl': open('service.wsdl', 'r').read()})


@app.route('/rest-adapter-service/Consumer/GetOpenAPI')
def get_openapi():
    return send_file('petstore.json')


@app.route('/rest-adapter-service/Consumer/IsSoapService')
def is_soap_service():
    xroad_instance = request.args.get('xRoadInstance')
    member_class = request.args.get('memberClass')
    member_code = request.args.get('memberCode')
    subsystem_code = request.args.get('subsystemCode')
    service_code = request.args.get('serviceCode')
    service_version = parse_service_version(request.args.get('serviceVersion'))

    member = find_member(DATA, xroad_instance, member_class, member_code)
    subsystem = find_subsystem(member, subsystem_code)
    service = find_service(subsystem, service_code, service_version)
    
    if service is None:
        print('No such service: {}.{}.{}.{}.{}.{}'.format(xroad_instance, member_class, member_code,
                                                          subsystem_code, service_code, service_version))
        return jsonify({'soap': False})
    
    return jsonify({'soap': 'wsdl' in service})


@app.route('/rest-adapter-service/Consumer/IsRestService')
def is_rest_service():
    xroad_instance = request.args.get('xRoadInstance')
    member_class = request.args.get('memberClass')
    member_code = request.args.get('memberCode')
    subsystem_code = request.args.get('subsystemCode')
    service_code = request.args.get('serviceCode')
    service_version = parse_service_version(request.args.get('serviceVersion'))

    member = find_member(DATA, xroad_instance, member_class, member_code)
    subsystem = find_subsystem(member, subsystem_code)
    service = find_service(subsystem, service_code, service_version)
    
    if service is None:
        print('No such service: {}.{}.{}.{}.{}.{}'.format(xroad_instance, member_class, member_code,
                                                          subsystem_code, service_code, service_version))
        return jsonify({'rest': False})
    
    return jsonify({'rest': 'openapi' in service})


@app.route('/rest-adapter-service/Consumer/HasCompanyChanged')
def has_company_changed():
    business_code = request.args.get('businessId')
    changed_after = request.args.get('changedAfter')
    return jsonify({'result': True})


@app.route('/rest-adapter-service/Consumer/HasOrganizationChanged')
def has_organization_changed():
    business_code = request.args.get('guid')
    changed_after = request.args.get('changedAfter')
    return jsonify({'result': True})


@app.route('/rest-adapter-service/Consumer/GetOrganizations')
def get_organizations():
    business_code = request.args.get('businessCode')
    return jsonify({'organizationList': {'organization': {}}})


@app.route('/rest-adapter-service/Consumer/GetCompanies')
def get_companies():
    business_code = request.args.get('businessId')
    return jsonify({'companyList': {'company': {}}})


def find_member(data, xroad_instance, member_class, member_code):
    return next((m for m in xroad_list_to_list(data, 'memberList', 'member')
                if m.get('xRoadInstance') == xroad_instance
                and m.get('memberClass') == member_class
                and m.get('memberCode') == member_code),
                None)


def find_subsystem(member, subsystem_code):
    if member is None:
        return None

    return next((s for s in xroad_list_to_list(member, 'subsystems', 'subsystem')
                if s.get('subsystemCode') == subsystem_code),
                None)


def find_service(subsystem, service_code, service_version):
    if subsystem is None:
        return None

    return next((s for s in xroad_list_to_list(subsystem, 'services', 'service')
                if s.get('serviceCode') == service_code
                and (parse_service_version(s.get('serviceVersion')) == service_version
                     or (not s.get('serviceVersion') and not service_version))),
                None)


def xroad_list_to_list(obj, key1, key2):
    maybe_list = (obj.get(key1) or {}).get(key2) or []
    if type(maybe_list) is list:
        return maybe_list
    elif type(maybe_list) is dict:
        return [maybe_list]
    else:
        return []


def parse_service_version(v):
    if v is None:
        return v
    elif type(v) in (str, unicode):
        return v
    elif type(v) in (int, float):
        return str(int(v))
    else:
        raise Exception('Unexpected service version type: {}'.format(repr(type(v))))

if __name__ == '__main__':
    app.run(port=9091)
