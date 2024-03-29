# -*- coding: utf-8 -*-
import settings
import datetime
import time
import json
import os
import re
import telnetlib
import traceback
import requests

logs = ''
if settings.DEBUG:
    logs = open(settings.log_file, 'a')
    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
               + "DEBUG: LOG FILE -- " + settings.log_file)

telnet_session = telnetlib.Telnet(settings.connection['address'], settings.connection['port'])
username = "Username: " + settings.login_data['username']
secret = "Secret: " + settings.login_data['secret']
ami_login = telnet_session.write("Action:login".encode('ascii') + b"\n"
                     + username.encode('ascii') + b"\n"
                     + secret.encode('ascii') + b"\n\n")

current_string = ''
result = {}
incoming_calls = {}
outgoing_calls = {}
timestamp_outgoing_answered = ''
timestamp_answer = ''
variables = {}
client_number = {}
item_dict = {}
subscriber_name = {}
start_timestamp = {}
connected_line = {}
end_timestamp = {}
event_timestamp = {}
event_name = {}
dial_status = {}
operator = {}
record_name = {}
record = {}
file_id = {}
payload = {}
all_logs = {}
file = {}
duration = {}
duration_result = {}
count = {}
login = {}
lid = {}
cdr_result = {}
current_operator = {}

if settings.DEBUG:
    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
               + "DEBUG: TELNET SESSION WITH ATTRIBUTES: "
               + settings.connection['address']
               + " "
               + str(settings.connection['port']))

while True:
    event_string = ''
    elements_string = ''
    read_some = telnet_session.read_some()
    string = read_some.decode('utf8', 'replace').replace('\r\n', '#')
    if '##' in str(string):
        string.replace('##', '##\r\n')

    if not string.endswith('##'):
        current_string = current_string + string

    if string.endswith('##'):
        current_string = current_string + string
        current_string = current_string.replace('##', '$') \
            .replace('\n', '#') \
            .replace('\r', '#') \
            .replace('"', '') \
            .replace('\\', '')

        events = re.findall(r'[A-Z][\w]+:\s[^$]+', current_string)
        for event in events:
            event_elements = re.findall(r'[A-Z][\w]+:\s[^#]+', event)

            for element in event_elements:
                element = '"' + element.replace(': ', '": "') + '\", '
                elements_string += element
            event_string += '"result": ' + '{' + elements_string + '}'
            event_string = event_string.replace('}{', '},{')
            event_string = event_string.replace(', }', '}, ')
        event_string = '{' + event_string + '}'
        event_string = event_string.replace('}, }', '}}')

        try:

            result = json.loads(event_string)
            if settings.DEBUG:
                logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                           + "DEBUG: CURRENT LINE -- " + str(result['result']))

            if 'Linkedid' in result['result']:
                if (result['result']['Linkedid'] in all_logs) is False:
                    all_logs[result['result']['Linkedid']] = str(result['result']) + "\n\n"
                elif "'Exten': 'h'" in str(result['result']) and \
                        (result['result']['Linkedid'] in all_logs) is True:
                    if result['result']['Linkedid'] in all_logs:
                        file[result['result']['Linkedid']] = open('/var/log/asterisk/call_logs/'
                                                                  + result['result']['Linkedid'], 'a')
                        all_logs[result['result']['Linkedid']] += str(result['result']) + "\n\n"
                        file[result['result']['Linkedid']].write(str(all_logs[result['result']['Linkedid']]))
                        file[result['result']['Linkedid']].close()
                else:
                    all_logs[result['result']['Linkedid']] += str(result['result']) + "\n\n"

            # INCOMING CALLS

            if (('NewCallerid' in result['result'].values() or 'MixMonitorStart' in result['result'].values())
                and 'check-abon' in result['result'].values()) is True:

                if (result['result']['Linkedid'] in outgoing_calls and
                    result['result']['Linkedid'] in incoming_calls) is False:

                    start_timestamp[result['result']['Linkedid']] = int(str(result['result']['Timestamp']) \
                                                                        .split('.')[0])

                    timestamp_answer = datetime.datetime.fromtimestamp(float(result['result']['Timestamp'])) \
                        .strftime("%M:%S")

                    current_operator[result['result']['Linkedid']] = '1/201-0'

                    if str(result['result']['CallerIDNum']).startswith('+'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum'][3:]
                    elif str(result['result']['CallerIDNum']).startswith('3'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum'][2:]
                    elif str(result['result']['CallerIDNum']).startswith('0'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum']
                    else:
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum']

                    if '<unknown>' in result['result']['CallerIDName']:
                        lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                            str(client_number[result['result']['Linkedid']]))
                        if lid[result['result']['Linkedid']] == '':
                            subscriber_name[result['result']['Linkedid']] = "[Найти]" \
                                                                            + "(" \
                                                                            + settings.elma_settings[
                                                                                'lid_search'] \
                                                                            + client_number[
                                                                                result['result']['Linkedid']] + '"%7D' \
                                                                            + ")" \
                                                                            + ' или [создать]' + "(" \
                                                                            + settings.elma_settings[
                                                                                'lid_create'] + ") лид"
                        else:
                            subscriber_name[result['result']['Linkedid']] = '[Лид: ' + \
                                                                            lid[result['result']['Linkedid']][1] + ']' \
                                                                            + "(" + settings.elma_settings['lid_link'] \
                                                                            + lid[result['result']['Linkedid']][0] \
                                                                            + "))"
                    else:
                        login[result['result']['Linkedid']] = str(client_number[result['result']['Linkedid']])
                        login[result['result']['Linkedid']] = settings.get_abills_uid(
                            str(login[result['result']['Linkedid']]))
                        subscriber_name[result['result']['Linkedid']] = '[Абонент: ' \
                                                                        + str(login[result['result']['Linkedid']][0]) \
                                                                        + ", " \
                                                                        + str(login[result['result']['Linkedid']][1]) \
                                                                        + ']' \
                                                                        + '(' + settings.abills_settings[
                                                                            'abon_link'] + str(
                            login[result['result']['Linkedid']][2]) + ')'
                        lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                            str(client_number[result['result']['Linkedid']]))
                        if lid[result['result']['Linkedid']] == '':
                            lid[result['result']['Linkedid']] = ''
                        else:
                            lid[result['result']['Linkedid']] = [lid[result['result']['Linkedid']][0]]

                    incoming_calls[result['result']['Linkedid']] = "/event/" \
                                                                   + "Поступил новый звонок" \
                                                                   + " ///DELIMITER/// " \
                                                                   + "/status/" \
                                                                   + "Звонок начат" \
                                                                   + " ///DELIMITER/// " \
                                                                   + "/time/" \
                                                                   + "00:00" \
                                                                   + " ///DELIMITER/// "

                    if settings.DEBUG:
                        logs.write(str("\n\n" + datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: INCOMING CALL STARTED WITH VALUES: \nCLIENT NUM: "
                                   + client_number[result['result']['Linkedid']])

            if ('Hangup' in result['result'].values()) is True and \
                    ('BUSY' in result['result'].values()) is False \
                    and result['result']['Linkedid'] in incoming_calls:

                end_timestamp[result['result']['Linkedid']] = int(str(result['result']['Timestamp']) \
                                                                  .split('.')[0])

                time.sleep(2)
                cdr_result[result['result']['Linkedid']] = settings.get_cdr_records(result['result']['Linkedid'])
                if settings.DEBUG:
                    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                               + "DEBUG: CDR VALUES FOR ID " + str(result['result']['Linkedid']) + " is "
                               + str(cdr_result[result['result']['Linkedid']]))

                employers = settings.get_employers_list()
                if settings.DEBUG:
                    logs.write(str("\n\n" + datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: EMPLOYERS LIST: " + str(employers))

                for records in cdr_result[result['result']['Linkedid']]:
                    if records['lastapp'] != 'Hangup':
                        event_timestamp[result['result']['Linkedid']] = '00:00'
                        dial_status[result['result']['Linkedid']] = 'DEFAULT'
                        event_name[result['result']['Linkedid']] = 'DEFAULT'
                        current_operator[result['result']['Linkedid']] = '1/201-0'

                        # SET CURRENT OPERATOR
                        if not records['dst_channel']:
                            current_operator[result['result']['Linkedid']] = '1/201-0'
                        else:
                            current_operator[result['result']['Linkedid']] = \
                                str(records['dst_channel'])
                        # GET STATUS
                        if records['status'] == 'BUSY':
                            dial_status[result['result']['Linkedid']] = 'Оператор занят, направлено другому оператору'
                        elif records['status'] == 'NO ANSWER':
                            dial_status[
                                result['result']['Linkedid']] = 'Оператор не отвечает или звонящий бросил трубку'
                        elif records['status'] == 'ANSWERED':
                            dial_status[result['result']['Linkedid']] = 'Отвечен, идёт разговор'
                        elif records['status'] == 'FAILED':
                            dial_status[result['result']['Linkedid']] = 'Ошибка во время звонка'
                        else:
                            dial_status[result['result']['Linkedid']] = 'Неизвестный статус'

                        # GET EVENT
                        if records['lastapp'] == 'Queue':
                            if 'Отвечен' not in dial_status[result['result']['Linkedid']]:

                                event_name[result['result']['Linkedid']] = 'Звонок оператору - ' \
                                                                           + str(records['dst_channel']) \
                                                                               .split('/')[1] \
                                                                               .split('-')[0]
                                if settings.DEBUG:
                                    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                               + "DEBUG: CALL EVENT: " + str(records))

                            else:
                                event_name[result['result']['Linkedid']] = 'Разговор с оператором - ' \
                                                                           + current_operator[result['result']['Linkedid']] \
                                                                               .split('/')[1] \
                                                                               .split('-')[0]
                                if settings.DEBUG:
                                    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                               + "DEBUG: ANSWERED EVENT: " + str(records))

                        elif records['lastapp'] == 'Dial':
                            if records['status'] != 'BUSY':
                                event_name[result['result']['Linkedid']] = 'Разговор с оператором - ' \
                                                                       + str(records['dst_channel']) \
                                                                           .split('/')[1] \
                                                                           .split('-')[0]
                                if settings.DEBUG:
                                    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                           + "DEBUG: DIAL EVENT, ANSWERED: " + str(records))
                            else:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору - ' \
                                                                           + str(records['dst_channel']) \
                                                                               .split('/')[1] \
                                                                               .split('-')[0]
                                if settings.DEBUG:
                                    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                               + "DEBUG: DIAL EVENT, NOT ANSWERED: " + str(records))

                        elif records['lastapp'] == 'AppQueue':
                            event_name[result['result']['Linkedid']] = 'Абонент был переведён'
                            dial_status[result['result']['Linkedid']] = 'Перевод звонка'
                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                           + "DEBUG: DIAL EVENT: " + str(records))

                        else:
                            if records['lastapp'] != 'Set':
                                event_name[result['result']['Linkedid']] = 'Неизвестное событие'
                                dial_status[result['result']['Linkedid']] = 'Неизвестный статус'
                                if settings.DEBUG:
                                    logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                               + "DEBUG: UNKNOWN EVENT, NEED TO CHECK: " + str(records))

                        # GET EVENT DURATION
                        if 'latency' in records:
                            event_timestamp[result['result']['Linkedid']] = str(datetime.timedelta(
                                seconds=records['latency']))[2:]
                        else:
                            event_timestamp[result['result']['Linkedid']] = '00:00'

                        incoming_calls[result['result']['Linkedid']] += "/event/" \
                                                                        + event_name[result['result']['Linkedid']] \
                                                                        + " ///DELIMITER/// " \
                                                                        + "/status/" \
                                                                        + dial_status[result['result']['Linkedid']] \
                                                                        + " ///DELIMITER/// " \
                                                                        + "/time/" \
                                                                        + event_timestamp[result['result']['Linkedid']] \
                                                                        + " ///DELIMITER/// "
                        # GET RECORD NAME
                        if records['record_name'] != '':
                            record_name[result['result']['Linkedid']] = records['record_name']
                        else:
                            record_name[result['result']['Linkedid']] = 'NO RECORD FILE'

                # GET OPERATOR
                for user in employers:
                    if user['number'] is None or int(user['number']) < 400:
                        if str(user['number']) == current_operator[result['result']['Linkedid']].split('/')[1].split('-')[0]:
                            operator[result['result']['Linkedid']] = [current_operator[result['result']['Linkedid']]\
                                                                          .split('/')[1]
                                                                          .split('-')[0],
                                                                      user['name']]

                if settings.DEBUG:
                    logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: OPERATOR: " + str(
                                    operator[result['result']['Linkedid']]))

                if settings.DEBUG:
                    if result['result']['Linkedid'] in record_name:
                        logs.write(str("\n\n" + datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: RECORD FILE NAME -- " +
                                   str(record_name[result['result']['Linkedid']]))

                if settings.DEBUG:
                    logs.write(str("\n\n" + datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: CURRENT EVENT DICT STATE -- " +
                               str(incoming_calls[result['result']['Linkedid']]))

                incoming_calls[result['result']['Linkedid']] += "/event/" + "Звонок завершён" \
                                                                + " ///DELIMITER/// " \
                                                                + "/status/" \
                                                                + "Звонок завершён" \
                                                                + " ///DELIMITER/// " \
                                                                + "/time/" \
                                                                + datetime.datetime.fromtimestamp(
                    (end_timestamp[result['result']['Linkedid']] - start_timestamp[result['result']['Linkedid']]) + 13) \
                                                                    .strftime('%M:%S')

                rows_split = incoming_calls[result['result']['Linkedid']].split(' ///DELIMITER/// ')
                rows = []

                for item in rows_split:
                    if '/event/' in item:
                        item_dict[result['result']['Linkedid']] = {"event": '', "status": '', "time": ''}
                        item_dict[result['result']['Linkedid']]['event'] = item.replace('/event/', '').replace(
                            '{', '').replace('}', '').replace('"', '').replace("'", '')

                    elif '/status/' in item:
                        item_dict[result['result']['Linkedid']]['status'] = item.replace('/status/', '')

                    elif '/time/' in item:
                        item_dict[result['result']['Linkedid']]['time'] = item.replace('/time/', '')
                        rows.append(item_dict[result['result']['Linkedid']])

                # os.system('ls /var/spool/asterisk/monitor/ >> /dev/null')
                if result['result']['Linkedid'] in record_name:
                    if ("Разговор" in str(incoming_calls[result['result']['Linkedid']])) is True:
                        if os.path.isfile('/var/spool/asterisk/monitor/' +
                                          str(record_name[result['result']['Linkedid']])):
                            record[result['result']['Linkedid']] = {"file": open(
                                '/var/spool/asterisk/monitor/' + str(
                                    record_name[result['result']['Linkedid']]),
                                'rb')}

                            api_upload_file = requests.post(settings.elma_settings['link']
                                                            + 'pub/v1/disk/directory/'
                                                            + settings.elma_settings[
                                                                'directory_id'] + '/upload',
                                                            files=record[result['result']['Linkedid']],
                                                            headers={
                                                                'X-Token': settings.elma_settings['token'],
                                                            })

                            file_id[result['result']['Linkedid']] = json.loads(api_upload_file.content)['file'][
                                '__id']
                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: FILE CREATE -- " + str(
                                    api_upload_file.content))

                        else:
                            file_id[result['result']['Linkedid']] = 'NONE'
                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: RECORD FILE NOT FOUND")

                    else:
                        file_id[result['result']['Linkedid']] = 'MISSED'
                        if settings.DEBUG:
                            logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: MISSED CALL, NO FILE UPLOADS NEEDED")


                else:
                    file_id[result['result']['Linkedid']] = 'NONE'
                    if settings.DEBUG:
                        logs.write(str("\n\n" + datetime.datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: RECORD FILE NOT FOUND")

                if result['result']['Linkedid'] in lid:
                    if lid[result['result']['Linkedid']] != '':
                        if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                and ('MISSED' in file_id[result['result']['Linkedid']]) is False:

                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "otvechen", "name": "📥Отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "record": [file_id[result['result']['Linkedid']]],
                                "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                "call_logs":
                                    {
                                        "rows": rows
                                    }
                            }
                            }
                        else:
                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "ne_otvechen", "name": "🔻Не отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                "call_logs":
                                    {
                                        "   rows": rows
                                    }
                            }
                            }
                    else:
                        if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                and ('MISSED' in file_id[result['result']['Linkedid']]) is False:

                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "otvechen", "name": "📥Отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "record": [file_id[result['result']['Linkedid']]],
                                "call_logs":
                                    {
                                        "rows": rows
                                    }
                            }
                            }
                        else:
                            payload[result['result']['Linkedid']] = {"context": {
                                "status_zvonka": [{"code": "ne_otvechen", "name": "🔻Не отвечен"}],
                                "type": [{"code": "vkhodyashii", "name": "Входящий"}],
                                "__name": str(client_number[result['result']['Linkedid']]),
                                "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                "poslednii_operator": operator[result['result']['Linkedid']][1],
                                "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                "call_logs":
                                    {
                                        "rows": rows
                                    }
                            }
                            }

                api_create_object = requests.post(settings.elma_settings['link'] + 'pub/v1/app/'
                                                  + settings.elma_settings['namespace'] + '/'
                                                  + settings.elma_settings['incoming_calls'] + '/create',
                                                  data=json.dumps(payload[result['result']['Linkedid']]),
                                                  headers={
                                                      'X-Token': settings.elma_settings['token'],
                                                  })

                incoming_calls.pop(result['result']['Linkedid'], None)
                client_number.pop(result['result']['Linkedid'], None)
                connected_line.pop(result['result']['Linkedid'], None)
                end_timestamp.pop(result['result']['Linkedid'], None)
                start_timestamp.pop(result['result']['Linkedid'], None)
                event_timestamp.pop(result['result']['Linkedid'], None)
                variables.pop(result['result']['Linkedid'], None)
                item_dict.pop(result['result']['Linkedid'], None)
                subscriber_name.pop(result['result']['Linkedid'], None)
                start_timestamp.pop(result['result']['Linkedid'], None)
                connected_line.pop(result['result']['Linkedid'], None)
                end_timestamp.pop(result['result']['Linkedid'], None)
                event_timestamp.pop(result['result']['Linkedid'], None)
                event_name.pop(result['result']['Linkedid'], None)
                dial_status.pop(result['result']['Linkedid'], None)
                file_id.pop(result['result']['Linkedid'], None)
                record.pop(result['result']['Linkedid'], None)
                record_name.pop(result['result']['Linkedid'], None)
                payload.pop(result['result']['Linkedid'], None)
                login.pop(result['result']['Linkedid'], None)
                lid.pop(result['result']['Linkedid'], None)
                file_id.pop(result['result']['Linkedid'], None)
                cdr_result.pop(result['result']['Linkedid'], None)
                current_operator.pop(result['result']['Linkedid'], None)

                if settings.DEBUG:
                    logs.write(str("\n\n" + datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: API RESPONSE -- " + str(
                        json.loads(api_create_object.content.decode('utf-8'))))

            # OUTGOING CALLS

            if ('Linkedid' in result['result'] and
                '202' not in result['result']['CallerIDNum']) is True:

                if (result['result']['Linkedid'] in incoming_calls) is False and \
                        (result['result']['Linkedid'] in outgoing_calls) is False:
                    if 'DialBegin' in result['result']['Event'] and 'callout' in result['result'].values() and \
                            result['result']['ChannelState'] == '4':
                        if 'DialString' in result['result']:
                            start_timestamp[result['result']['Linkedid']] = int(
                                str(result['result']['Timestamp']).split('.')[0])
                            client_number[result['result']['Linkedid']] = \
                                str(result['result']['DialString']).split('@')[0]
                            outgoing_calls[result['result']['Linkedid']] = "/event/" \
                                                                           + "Звонок на номер " \
                                                                           + client_number[result['result']['Linkedid']] \
                                                                           + " ///DELIMITER/// " \
                                                                           + "/status/" \
                                                                           + "Звонок начался" \
                                                                           + " ///DELIMITER/// " \
                                                                           + "/time/" + "00:00" \
                                                                           + " ///DELIMITER/// "

                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                           + 'DEBUG: OUTGOING CALL STARTED WITH VALUES: \nCLIENT NUM: '
                                           + client_number[result['result']['Linkedid']])

                if (result['result']['Linkedid'] in outgoing_calls) is True \
                        and (result['result']['Linkedid'] in incoming_calls) is False:

                    if ('DialBegin' in result['result']['Event']) is False and \
                            ('Exten' in result['result']) is True:

                        if result['result']['Exten'] == 'h' and \
                                ('Hangup' in str(result['result'].values())) is True or \
                                ('QueueMemberStatus' in result['result'].values()) is True:

                            timestamp_outgoing_finished = datetime.datetime.fromtimestamp(
                                float(result['result']['Timestamp'])) \
                                .strftime("%H:%M:%S")
                            end_timestamp[result['result']['Linkedid']] = datetime.datetime.fromtimestamp(
                                int(str(result['result']['Timestamp']).split('.')[0]) -
                                start_timestamp[result['result']['Linkedid']]).strftime("%M:%S")

                            login[result['result']['Linkedid']] = str(client_number[result['result']['Linkedid']])
                            login[result['result']['Linkedid']] = settings.get_abills_uid(
                                str(login[result['result']['Linkedid']]))

                            if ('NONE' in str(login[result['result']['Linkedid']])) is True:
                                lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                                    str(client_number[result['result']['Linkedid']]))
                                if lid[result['result']['Linkedid']] == '':
                                    subscriber_name[result['result']['Linkedid']] = "[Найти]" \
                                                                                    + "(" \
                                                                                    + settings.elma_settings[
                                                                                        'lid_search'] \
                                                                                    + client_number[
                                                                                        result['result'][
                                                                                            'Linkedid']] \
                                                                                    + '"%7D' \
                                                                                    + ")" + "  " \
                                                                                            "" \
                                                                                    + 'или [создать]' + "(" \
                                                                                    + settings.elma_settings[
                                                                                        'lid_create'] + ") лид"
                                else:
                                    subscriber_name[result['result']['Linkedid']] = '[Лид: ' + \
                                                                                    lid[result['result'][
                                                                                        'Linkedid']][
                                                                                        1] + ']' \
                                                                                    + "(" + settings.elma_settings[
                                                                                        'lid_link'] \
                                                                                    + lid[result['result'][
                                        'Linkedid']][0] \
                                                                                    + "))"
                            else:
                                subscriber_name[result['result']['Linkedid']] = '[Абонент: ' \
                                                                                + str(
                                    login[result['result']['Linkedid']][0]) \
                                                                                + ", " \
                                                                                + str(
                                    login[result['result']['Linkedid']][1]) \
                                                                                + ']' \
                                                                                + '(' + settings.abills_settings[
                                                                                    'abon_link'] + str(
                                    login[result['result']['Linkedid']][2]) + ')'
                                lid[result['result']['Linkedid']] = settings.get_elma_lid_id(
                                    str(client_number[result['result']['Linkedid']]))
                                if lid[result['result']['Linkedid']] == '':
                                    lid[result['result']['Linkedid']] = ''
                                else:
                                    lid[result['result']['Linkedid']] = [lid[result['result']['Linkedid']][0]]

                            time.sleep(2)
                            cdr_result[result['result']['Linkedid']] = settings.get_cdr_records(result['result']['Linkedid'])
                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                           + "DEBUG: CDR VALUES FOR ID " + str(result['result']['Linkedid']) + ' is '
                                           + str(cdr_result[result['result']['Linkedid']]))

                            employers = settings.get_employers_list()
                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: EMPLOYERS LIST: " + str(employers))

                            for records in cdr_result[result['result']['Linkedid']]:
                                if records['lastapp'] != 'Hangup':

                                    # SET CURRENT OPERATOR
                                    current_operator[result['result']['Linkedid']] = str(records['channel']) \
                                        .split('/')[1] \
                                        .split('-')[0]
                                    # GET STATUS
                                    if records['status'] == 'BUSY':
                                        dial_status[result['result'][
                                            'Linkedid']] = 'Абонент занят'
                                    elif records['status'] == 'NO ANSWER':
                                        dial_status[result['result'][
                                            'Linkedid']] = 'Абонент не отвечает'
                                    elif records['status'] == 'ANSWERED':
                                        dial_status[result['result']['Linkedid']] = 'Отвечен, идёт разговор'
                                    elif records['status'] == 'FAILED':
                                        dial_status[result['result']['Linkedid']] = 'Абонент не отвечает'
                                    else:
                                        dial_status[result['result']['Linkedid']] = 'Неизвестный статус'

                                    # GET EVENT
                                    if records['lastapp'] == 'Queue' and len(str(records['number'])) <= 3:
                                        if 'Отвечен' not in dial_status[result['result']['Linkedid']]:

                                            event_name[result['result']['Linkedid']] = 'Звонок абоненту, оператор - ' \
                                                                                       + str(records['number'])
                                            if settings.DEBUG:
                                                logs.write(
                                                    str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                                    + "DEBUG: CALL EVENT: " + str(records))

                                        else:
                                            event_name[
                                                result['result']['Linkedid']] = 'Разговор с абонентом, оператор - ' \
                                                                                + str(records['number'])
                                            if settings.DEBUG:
                                                logs.write(
                                                    str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                                    + "DEBUG: ANSWERED EVENT: " + str(records))

                                    elif records['lastapp'] == 'Dial' and len(str(records['number'])) <= 3:
                                        if records['status'] == 'ANSWERED':
                                            event_name[
                                                result['result']['Linkedid']] = 'Разговор с абонентом, оператор - ' \
                                                                                + str(records['number'])
                                        else:
                                            event_name[result['result']['Linkedid']] = 'Звонок абоненту, оператор - ' \
                                                                                       + str(records['number'])
                                        if settings.DEBUG:
                                            logs.write(
                                                str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                                + "DEBUG: DIAL EVENT: " + str(records))

                                    else:
                                        if len(str(records['number'])) <= 3:
                                            event_name[result['result']['Linkedid']] = 'Неизвестное событие'
                                            if settings.DEBUG:
                                                logs.write(
                                                    str("\n\n" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S -- "))
                                                    + "DEBUG: UNKNOWN EVENT, NEED TO CHECK: " + str(records))

                                    # GET EVENT DURATION
                                    if 'latency' in records:
                                        event_timestamp[result['result']['Linkedid']] = str(datetime.timedelta(
                                            seconds=records['latency']))[2:]
                                    else:
                                        event_timestamp[result['result']['Linkedid']] = '00:00'

                                    outgoing_calls[result['result']['Linkedid']] += "/event/" \
                                                                                    + event_name[
                                                                                        result['result']['Linkedid']] \
                                                                                    + " ///DELIMITER/// " \
                                                                                    + "/status/" \
                                                                                    + dial_status[
                                                                                        result['result']['Linkedid']] \
                                                                                    + " ///DELIMITER/// " \
                                                                                    + "/time/" \
                                                                                    + event_timestamp[
                                                                                        result['result']['Linkedid']] \
                                                                                    + " ///DELIMITER/// "
                                    # GET RECORD NAME
                                    if records['record_name'] != '':
                                        record_name[result['result']['Linkedid']] = records['record_name']
                                    else:
                                        record_name[result['result']['Linkedid']] = 'NO RECORD FILE'
                            # GET OPERATOR
                            for user in employers:
                                if str(user['number']) == current_operator[result['result']['Linkedid']]:
                                    operator[result['result']['Linkedid']] = [
                                        current_operator[result['result']['Linkedid']],
                                        user['name']]
                                    break

                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %M:%S -- ")) + "DEBUG: OPERATOR: " + str(
                                    operator[result['result']['Linkedid']]))

                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: RECORD FILE NAME -- " +
                                           str(record_name[result['result']['Linkedid']]))

                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: CURRENT EVENT DICT STATE -- " +
                                           str(outgoing_calls[result['result']['Linkedid']]))

                            outgoing_calls[result['result']['Linkedid']] += "/event/" + "Звонок завершён" \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/status/" + "Конец звонка" \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/time/" \
                                                                            + end_timestamp[
                                                                                result['result']['Linkedid']]

                            rows_split = outgoing_calls[result['result']['Linkedid']].split(' ///DELIMITER/// ')
                            rows = []

                            for item in rows_split:
                                if '/event/' in item:
                                    item_dict[result['result']['Linkedid']] = {"event": '', "status": '', "time": ''}
                                    item_dict[result['result']['Linkedid']]['event'] = item.replace('/event/', '') \
                                        .replace('{', '') \
                                        .replace('}', '') \
                                        .replace('"', '') \
                                        .replace("'", '')

                                elif '/status/' in item:
                                    item_dict[result['result']['Linkedid']]['status'] = item.replace('/status/', '')

                                elif '/time/' in item:
                                    item_dict[result['result']['Linkedid']]['time'] = item.replace('/time/', '')
                                    rows.append(item_dict[result['result']['Linkedid']])

                            # os.system('ls /home/fishhead/asterisk/records/ >> /dev/null')
                            if result['result']['Linkedid'] in record_name:
                                if 'Разговор' in outgoing_calls[result['result']['Linkedid']]:
                                    if os.path.isfile('/var/spool/asterisk/monitor/' + str(
                                            record_name[result['result']['Linkedid']])):
                                        record[result['result']['Linkedid']] = {"file": open(
                                            '/var/spool/asterisk/monitor/' + str(
                                                record_name[result['result']['Linkedid']]),
                                            'rb')}

                                        api_upload_file = requests.post(settings.elma_settings['link']
                                                                        + 'pub/v1/disk/directory/'
                                                                        + settings.elma_settings[
                                                                            'directory_id'] + '/upload',
                                                                        files=record[result['result']['Linkedid']],
                                                                        headers={
                                                                            'X-Token': settings.elma_settings['token'],
                                                                        })

                                        file_id[result['result']['Linkedid']] = \
                                            json.loads(api_upload_file.content)['file'][
                                                '__id']

                                        if settings.DEBUG:
                                            logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                                "%Y-%m-%d %M:%S -- ")) + "DEBUG: FILE CREATE -- " + str(
                                                api_upload_file.content))

                                    else:
                                        file_id[result['result']['Linkedid']] = 'NONE'
                                        if settings.DEBUG:
                                            logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                                "%Y-%m-%d %M:%S -- ")) + "DEBUG: RECORD FILE NOT FOUND")

                                else:
                                    file_id[result['result']['Linkedid']] = 'NOANSWER'
                                    if settings.DEBUG:
                                        logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                            "%Y-%m-%d %M:%S -- ")) + "DEBUG: DID NOT GET ANSWER, NO RECORD FILE NEEDED")

                            if result['result']['Linkedid'] in lid:
                                if lid[result['result']['Linkedid']] != '':
                                    if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                            and ('NOANSWER' in file_id[result['result']['Linkedid']]) is False:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "otvechen_1", "name": "📤Отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                            "record": [file_id[result['result']['Linkedid']]],
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }
                                    else:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "ne_otvechen_1", "name": "🔺Не отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "svyazannye_lidy": [lid[result['result']['Linkedid']][0]],
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }
                                else:
                                    if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                            and ('NOANSWER' in file_id[result['result']['Linkedid']]) is False:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "otvechen_1", "name": "📤Отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "record": [file_id[result['result']['Linkedid']]],
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }
                                    else:
                                        payload[result['result']['Linkedid']] = {"context": {
                                            "status_zvonka": [{"code": "ne_otvechen_1", "name": "🔺Не отвечен"}],
                                            "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                            "__name": str(client_number[result['result']['Linkedid']]),
                                            "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                            "poslednii_operator": operator[result['result']['Linkedid']][1],
                                            "abonent": str(subscriber_name[result['result']['Linkedid']]),
                                            "call_logs":
                                                {
                                                    "rows": rows
                                                }
                                        }
                                        }

                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: PAYLOAD CONTEXT: " + str(
                                    payload[result['result']['Linkedid']]))

                            api_create_object = requests.post(settings.elma_settings['link'] + 'pub/v1/app/'
                                                              + settings.elma_settings['namespace'] + '/'
                                                              + settings.elma_settings['outgoing_calls'] + '/create',
                                                              data=json.dumps(payload[result['result']['Linkedid']]),
                                                              headers={
                                                                  'X-Token': settings.elma_settings['token'],
                                                              })

                            if settings.DEBUG:
                                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: API RESPONSE -- "
                                           + str(json.loads(api_create_object.content)))

                            outgoing_calls.pop(result['result']['Linkedid'], None)
                            client_number.pop(result['result']['Linkedid'], None)
                            operator.pop(result['result']['Linkedid'], None)
                            connected_line.pop(result['result']['Linkedid'], None)
                            end_timestamp.pop(result['result']['Linkedid'], None)
                            start_timestamp.pop(result['result']['Linkedid'], None)
                            event_timestamp.pop(result['result']['Linkedid'], None)
                            variables.pop(result['result']['Linkedid'], None)
                            item_dict.pop(result['result']['Linkedid'], None)
                            subscriber_name.pop(result['result']['Linkedid'], None)
                            start_timestamp.pop(result['result']['Linkedid'], None)
                            connected_line.pop(result['result']['Linkedid'], None)
                            end_timestamp.pop(result['result']['Linkedid'], None)
                            event_timestamp.pop(result['result']['Linkedid'], None)
                            event_name.pop(result['result']['Linkedid'], None)
                            dial_status.pop(result['result']['Linkedid'], None)
                            payload.pop(result['result']['Linkedid'], None)
                            login.pop(result['result']['Linkedid'], None)
                            lid.pop(result['result']['Linkedid'], None)
                            file_id.pop(result['result']['Linkedid'], None)
                            cdr_result.pop(result['result']['Linkedid'], None)
                            current_operator.pop(result['result']['Linkedid'], None)

        except Exception:
            if settings.DEBUG:
                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S -- ")) + "DEBUG: TRACEBACK ERROR -- " + str(traceback.format_exc()))
            else:
                pass
        except json.decoder.JSONDecodeError as json_error:
            if settings.DEBUG:
                logs.write(str("\n\n" + datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S --")) + "DEBUG: JSON DECODER ERROR, ARGS: \n ERROR NAME: " + str(json_error)
                           + "\nLINE: " + str(event_string))
            else:
                pass

        current_string = ''
