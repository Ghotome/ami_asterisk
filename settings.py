import json

import mysql.connector as mysql
import requests

DEBUG = True

connection = {
    'address': '172.16.10.101',
    'port': 5038
}

login_data = {
    'username': 'test',
    'secret': '11223344'
}

elma_settings = {
    'link': 'https://elma.dianet.com.ua/',
    'token': '05fac167-689a-476d-9e7e-d52c14890dd7',
    'namespace': 'CRM_Dianet',
    'outgoing_calls': 'calls_all',
    'incoming_calls': 'calls_all',
    'lidy': 'lidy',
    'directory_id': '796115c4-90a8-4962-93a8-477e90fecae0',
    'employers': '_system_catalogs/sotrudniki',
    'lid_link': 'https://elma.dianet.com.ua/CRM_Dianet/lidy(p:item/CRM_Dianet/lidy/',
    'lid_create': 'https://elma.dianet.com.ua/CRM_Dianet/lidy(p:item/CRM_Dianet/lidy)',
    'lid_search': 'https://elma.dianet.com.ua/CRM_Dianet/lidy?search=%7B"simple":"'
}

abills_settings = {
    'abon_link': 'https://abill.dianet.com.ua:9443/admin/index.cgi?index=15&UID='
}

mysql_settings = {
    'host': '172.16.10.101',
    'user': 'ami',
    'secret': 'fkxK7JveMdvtp8',
    'db': 'asteriskcdrdb'
}


def get_cdr_records(linkedid):
    db = mysql.connect(host=mysql_settings['host'],
                       user=mysql_settings['user'],
                       passwd=mysql_settings['secret'],
                       database=mysql_settings['db'])
    result = []
    keys = ['number', 'login', 'channel', 'dst_channel', 'lastapp', 'latency', 'status', 'record_name']
    cursor = db.cursor()
    cursor.execute(
        'select src, clid, channel, dstchannel, lastapp, billsec, disposition, recordingpath from cdr where linkedid ='
        + str(linkedid))
    values = cursor.fetchall()
    for value in values:
        result.append(dict(zip(keys, value)))

    return result


def get_employers_list():
    var = {"size": 100}
    employers = []

    employers_list = requests.post('https://elma.dianet.com.ua/pub/v1/app/_system_catalogs/sotrudniki/list',
                                   data=json.dumps(var),
                                   headers={
                                           'X-Token': elma_settings['token']
                                       })

    for user in json.loads(employers_list.content)['result']['result']:
        if 'asterisk_id' in user:
            employers.append({'id': user['__id'], 'name': user['polzovatel'], 'number': user['asterisk_id']})

    return employers


def get_abills_uid(serching_param):
    link = "https://abill.dianet.com.ua:9443/admin/index.cgi?qindex=7&search=1&type=10&header=1&json=1&LOGIN=" + \
           str(serching_param) + "&EXPORT_CONTENT=USERS_LIST&API_KEY=sdfgljkshdfghjdf2345js"

    user = ''

    get_abon_request = requests.get(link)
    if str(b'{\n\n}') in str(get_abon_request.content):
        user = ['NONE, NONE, NONE']
    else:
        result = json.loads(get_abon_request.content.decode('utf-8'))['DATA_1']

        for abon in result:
            if str(abon['login']) == str(serching_param):
                user = [abon['login'], abon['fio'], abon['uid']]
                break
            elif str(serching_param) in str(abon):
                user = [abon['login'], abon['fio'], abon['uid']]
            else:
                pass
    return user


def get_elma_lid_id(number):
    var = {
        'active': True,
        'size': 100
    }
    lids = ''

    get_lids_list = requests.post('https://elma.dianet.com.ua/pub/v1/app/CRM_Dianet/lidy/list',
                                  data=json.dumps(var),
                                  headers={
                                      'X-Token': elma_settings['token']
                                  })
    for lid in json.loads(get_lids_list.content.decode('utf-8'))['result']['result']:
        if str(number) in str(lid['nomer_telefona_txt']):
            lids = [lid['__id'], lid['__name']]
            break
        else:
            pass

    return lids
