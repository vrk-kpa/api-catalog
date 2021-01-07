from flask import Flask
import json
from io import open

from datetime import datetime, timedelta

app = Flask(__name__)


@app.route('/getListOfServices/<int:days>')
def getListOfServices(days=1):
    now = datetime.now()
    mock_data = json.load(open('getListOfServices.json', 'r', encoding='utf-8'))
    member_data = []
    for i in range(days):
        dt = now - timedelta(days=i)
        date = [dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond]
        member_data.append({'date': date, 'memberDataList': mock_data['memberData'][0]['memberDataList']})

    data = {'memberData': member_data, 'securityServerData': mock_data['securityServerData']}
    return json.dumps(data)


if __name__ == '__main__':
    app.run(port=8088)
