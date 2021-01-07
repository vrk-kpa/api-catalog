from flask import Flask, send_file, jsonify

app = Flask(__name__)


@app.route('/rest-adapter-service/Consumer/ListMembers')
def list_members():
    return send_file('listMembers.json')


@app.route('/rest-adapter-service/Consumer/IsProvider')
def is_provider():
    return jsonify({'provider': True})


@app.route('/rest-adapter-service/Consumer/GetWsdl')
def get_wsdl():
    return jsonify({'wsdl': open('service.wsdl', 'r').read()})


@app.route('/rest-adapter-service/Consumer/GetOpenAPI')
def get_openapi():
    return send_file('petstore.json')


@app.route('/rest-adapter-service/Consumer/IsSoapService')
def is_soap_service():
    return jsonify({'soap': True})


@app.route('/rest-adapter-service/Consumer/IsRestService')
def is_rest_service():
    return jsonify({'rest': False})


if __name__ == '__main__':
    app.run(port=9091)
