import json

import requests

DEBUG = True

connection = {
    'address': '172.16.10.101',
    'port': 5038
}

login_data = {
    'username': 'test1',
    'secret': '11223344'
}

elma_settings = {
    'link': 'https://elma.dianet.com.ua/',
    'token': '05fac167-689a-476d-9e7e-d52c14890dd7',
    'namespace': 'CRM_Dianet',
    'outgoing_calls': 'calls_all',
    'incoming_calls': 'calls_all',
    'directory_id': '796115c4-90a8-4962-93a8-477e90fecae0',
    'employers': '_system_catalogs/sotrudniki'
}


def get_employers_list():
    var = {"size": 100}
    employers = []

    get_employers_list = requests.post('https://elma.dianet.com.ua/pub/v1/app/_system_catalogs/sotrudniki/list',
                                       data=json.dumps(var),
                                       headers={
                                           'X-Token': elma_settings['token']
                                       })

    for user in json.loads(get_employers_list.content)['result']['result']:
        if 'asterisk_id' in user:
            employers.append({'id': user['__id'], 'name': user['polzovatel'], 'number': user['asterisk_id']})

    return employers
