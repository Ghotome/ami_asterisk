# -*- coding: utf-8 -*-

import datetime
import json
import os
import re
import telnetlib

import requests

import settings

telnet_session = telnetlib.Telnet(settings.connection['address'], settings.connection['port'])
username = "Username: " + settings.login_data['username']
secret = "Secret: " + settings.login_data['secret']
telnet_session.write("Action:login".encode('ascii') + b"\n"
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

while True:
    event_string = ''
    elements_string = ''
    read_some = telnet_session.read_some()
    string = read_some.decode('utf8', 'replace').replace('\r\n', '#')

    if not string.endswith('##'):
        current_string = current_string + string

    if string.endswith('##'):
        current_string = current_string + string
        current_string = current_string.replace('##', '$')
        current_string = current_string.replace('\n', '#')
        current_string = current_string.replace('\r', '#')
        current_string = current_string.replace('"', '')
        current_string = current_string.replace('\\', '')

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
                print("DEBUG: CURRENT LINE -- " + str(result['result']))
            else:
                continue
            if 'Linkedid' in result['result']:
                if (result['result']['Linkedid'] in all_logs) is False:
                    all_logs[result['result']['Linkedid']] = str(result['result']) + "\n\n"
                elif "'Exten': 'h'" in str(result['result']) and \
                        (result['result']['Linkedid'] in all_logs) is True:
                    if result['result']['Linkedid'] in all_logs:
                        file[result['result']['Linkedid']] = open('/home/fishhead/asterisk/all_logs/'
                                                                  + result['result']['Linkedid'], 'a')
                        all_logs[result['result']['Linkedid']] += str(result['result']) + "\n\n"
                        file[result['result']['Linkedid']].write(str(all_logs[result['result']['Linkedid']]))
                        file[result['result']['Linkedid']].close()
                else:
                    all_logs[result['result']['Linkedid']] += str(result['result']) + "\n\n"

            # INCOMING CALLS

            if ('MixMonitorStart' in result['result'].values() and
                'check-abon' in result['result'].values()) is True:

                if (result['result']['Linkedid'] in outgoing_calls and
                    result['result']['Linkedid'] in incoming_calls) is False:

                    start_timestamp[result['result']['Linkedid']] = int(str(result['result']['Timestamp']) \
                                                                        .split('.')[0])

                    timestamp_answer = datetime.datetime.fromtimestamp(float(result['result']['Timestamp'])) \
                        .strftime("%M:%S")

                    if str(result['result']['CallerIDNum']).startswith('+'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum'][3:]
                    elif str(result['result']['CallerIDNum']).startswith('3'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum'][2:]
                    elif str(result['result']['CallerIDNum']).startswith('0'):
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum']
                    else:
                        client_number[result['result']['Linkedid']] = result['result']['CallerIDNum']

                    record_name[result['result']['Linkedid']] = datetime.datetime.now().strftime('%Y-%m-%d-%H%M') \
                                                                + "-" + client_number[result['result']['Linkedid']] \
                                                                + ".wav"
                    if '<unknown>' in result['result']['CallerIDName']:
                        subscriber_name[result['result']['Linkedid']] = 'АБОНЕНТ НЕ НАЙДЕН'
                    else:
                        subscriber_name[result['result']['Linkedid']] = result['result']['CallerIDName']

                    if settings.DEBUG:
                        print("DEBUG: INCOMING CALL STARTED WITH VALUES: \nCLIENT NUM: "
                              + client_number[result['result']['Linkedid']]
                              + "\nRECORD NAME: " + record_name[result['result']['Linkedid']])
                    else:
                        continue

                    incoming_calls[result['result']['Linkedid']] = "/event/" + "Входящий звонок от " \
                                                                   + str(client_number[result['result']['Linkedid']]) \
                                                                   + " ///DELIMITER/// " \
                                                                   + "/status/" + "Звонок начат" \
                                                                   + " ///DELIMITER/// " \
                                                                   + "/time/" + "00:00" \
                                                                   + " ///DELIMITER/// "

            if ('Linkedid' in result['result']) is True:
                if (result['result']['Linkedid'] in incoming_calls) is True \
                        and (result['result']['Linkedid'] in outgoing_calls) is False:

                    if ('MixMonitorStart' in result['result'].values()) is False \
                            and ('Hangup' in result['result'].values()) is False \
                            and ('SoftHangupRequest' in result['result'].values()) is False \
                            and ('BridgeDestroy' in result['result'].values()) is False \
                            and ('BridgeLeave' in result['result'].values()) is False \
                            and ('QueueMemberStatus' in result['result'].values()) is False \
                            and ('DeviceStateChange' in result['result'].values()) is False \
                            and (result['result']['Linkedid'] in incoming_calls) is True:

                        timestamp_any_events = datetime.datetime.fromtimestamp(float(result['result']['Timestamp'])) \
                            .strftime("%H:%M:%S")
                        event_timestamp[result['result']['Linkedid']] = int(str(result['result']['Timestamp']) \
                                                                            .split('.')[0])

                        if 'BridgeEnter' in result['result']['Event']:
                            if ' ' not in result['result']['ConnectedLineName']:
                                event_name[result['result']['Linkedid']] = 'Разговор с оператором ' \
                                                                           + result['result']['ConnectedLineName']
                                dial_status[result['result']['Linkedid']] = 'Звонок в процессе'
                            else:
                                event_name[result['result']['Linkedid']] = 'Разговор с оператором ' \
                                                                           + result['result']['CallerIDName']
                                dial_status[result['result']['Linkedid']] = 'Звонок в процессе'
                        elif 'MusicOnHoldStart' in result['result']['Event']:
                            event_name[result['result']['Linkedid']] = 'Звонок переведён'
                            dial_status[result['result']['Linkedid']] = 'Звонок на удержании'
                        elif 'QueueCallerJoin' in result['result']['Event']:
                            if result['result']['Queue'] == 'queue_softphone':
                                event_name[result['result']['Linkedid']] = 'Звонок попал в очередь к техподдержке'
                                dial_status[result['result']['Linkedid']] = 'Начаты попытки дозвониться'
                            elif result['result']['Queue'] == 'queue_phone_manager':
                                event_name[result['result']['Linkedid']] = 'Звонок попал в очередь к коммерческому'
                                dial_status[result['result']['Linkedid']] = 'Начаты попытки дозвониться'
                        elif 'NewConnectedLine' in result['result']['Event']:
                            if ' ' not in result['result']['ConnectedLineName']:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + result['result']['ConnectedLineName']
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                            else:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + result['result']['CallerIDName']
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                        elif 'DialStatus' in result['result']:
                            if 'BUSY' in result['result']['DialStatus']:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + str(result['result']['DestCallerIDName'])
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                            elif 'RING' in result['result']['DialStatus']:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + str(result['result']['DestCallerIDName'])
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                            elif 'ANSWER' in result['result']['DialStatus']:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + str(result['result']['DestCallerIDName'])
                                dial_status[result['result']['Linkedid']] = 'Звонок в процессе'
                            elif 'NOANSWER' in result['result']['DialStatus']:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + str(result['result']['DestCallerIDName'])
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                            elif 'Up' in result['result']['DialStatus']:
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + str(result['result']['DestCallerIDName'])
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                        else:
                            if '<unknown>' not in str(result['result']['CallerIDName']) and \
                                    ' ' not in str(result['result']['CallerIDName']):
                                event_name[result['result']['Linkedid']] = 'Звонок оператору ' \
                                                                           + str(result['result']['CallerIDName'])
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                                if settings.DEBUG:
                                    print("DEBUG: UNKNOWN STATUS >> DEFAULT USED: " + str(result))
                                else:
                                    continue
                            else:
                                event_name[result['result']['Linkedid']] = 'Звонок к оператору ' \
                                                                           + str(result['result']['ConnectedLineName'])
                                dial_status[result['result']['Linkedid']] = 'Оператор занят'
                                if settings.DEBUG:
                                    print("DEBUG: UNKNOWN STATUS >> DEFAULT USED: " + str(result))
                                else:
                                    continue

                        if 'Callback' in str(result['result'].values()):
                            dial_status[result['result']['Linkedid']] = 'Клиент оставил просьбу перезвонить'

                        incoming_calls[result['result']['Linkedid']] += "/event/" \
                                                                        + event_name[result['result']['Linkedid']] \
                                                                        + " ///DELIMITER/// " \
                                                                        + "/status/" + str(
                            dial_status[result['result']['Linkedid']]) \
                                                                        + " ///DELIMITER/// " \
                                                                        + "/time/" \
                                                                        + datetime.datetime.fromtimestamp(
                            event_timestamp[result['result']['Linkedid']]
                            - start_timestamp[result['result']['Linkedid']]) \
                                                                            .strftime('%M:%S') \
                                                                        + " ///DELIMITER/// "

                    if result['result']['Exten'] == 'h' and \
                            ('Hangup' in result['result'].values() or
                             'QueueMemberStatus' in result['result'].values()) is True and \
                            result['result']['Linkedid'] in incoming_calls:

                        employers = settings.get_employers_list()
                        if settings.DEBUG:
                            print("DEBUG: EMPLOYERS LIST: " + str(employers))
                        else:
                            continue

                        end_timestamp[result['result']['Linkedid']] = int(str(result['result']['Timestamp']) \
                                                                          .split('.')[0])
                        timestamp_finished_call = datetime.datetime \
                            .fromtimestamp(float(result['result']['Timestamp'])) \
                            .strftime("%H:%M:%S")

                        if result['result']['Linkedid'] in dial_status:
                            if 'перезвонить' in str(dial_status[result['result']['Linkedid']]):
                                dial_status[result['result']['Linkedid']] = 'Клиент оставил просьбу перезвонить'

                        if 'Callback' in str(result['result'].values()):
                            dial_status[result['result']['Linkedid']] = 'Клиент оставил просьбу перезвонить'
                        else:
                            dial_status[result['result']['Linkedid']] = 'Конец звонка'

                        if 'перезвонить' in str(dial_status[result['result']['Linkedid']]):
                            operator[result['result']['Linkedid']] = ['Callback', 'Callback']

                        if len(str(result['result']['ConnectedLineNum'])) <= 3 or \
                                len(str(result['result']['CallerIDNum'])) <= 3:
                            for number in employers:
                                if str(number['number']) == str(result['result']['ConnectedLineNum']):
                                    operator[result['result']['Linkedid']] = [result['result']['ConnectedLineNum'],
                                                                              number['name']]
                                    if '<unknown>' in result['result']['CallerIDName']:
                                        operator[result['result']['Linkedid']] = [result['result']['ConnectedLineNum'],
                                                                                  number['name']]
                                    if settings.DEBUG:
                                        print("DEBUG: OPERATOR -- " + str(operator[result['result']['Linkedid']]))
                                    else:
                                        continue
                                    break
                                if str(number['number']) == str(result['result']['CallerIDNum']):
                                    operator[result['result']['Linkedid']] = [result['result']['CallerIDNum'],
                                                                              number['name']]
                                    if '<unknown>' in result['result']['ConnectedLineName']:
                                        operator[result['result']['Linkedid']] = [result['result']['CallerIDNum'],
                                                                                  number['name']]
                                    if settings.DEBUG:
                                        print("DEBUG: OPERATOR -- " + str(operator[result['result']['Linkedid']]))
                                    else:
                                        continue
                                    break

                        incoming_calls[result['result']['Linkedid']] += "/event/" + "Звонок завершён" \
                                                                        + " ///DELIMITER/// " \
                                                                        + "/status/" \
                                                                        + dial_status[result['result']['Linkedid']] \
                                                                        + " ///DELIMITER/// " \
                                                                        + "/time/" + str(datetime.datetime \
                                                                                         .fromtimestamp(end_timestamp[
                                                                                                            result[
                                                                                                                'result'][
                                                                                                                'Linkedid']]
                                                                                                        -
                                                                                                        start_timestamp[
                                                                                                            result[
                                                                                                                'result'][
                                                                                                                'Linkedid']])
                                                                                         .strftime("%M:%S"))

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

                        os.system('ls /home/fishhead/asterisk/records/ >> /dev/null')
                        if result['result']['Linkedid'] in record_name:
                            if ("Разговор" in str(incoming_calls[result['result']['Linkedid']])) is True:
                                if os.path.isfile('/home/fishhead/asterisk/records/' +
                                                  str(record_name[result['result']['Linkedid']])):
                                    record[result['result']['Linkedid']] = {"file": open(
                                        '/home/fishhead/asterisk/records/' + str(
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
                                        print("DEBUG: FILE CREATE -- " + str(api_upload_file.content))
                                    else:
                                        continue
                                else:
                                    file_id[result['result']['Linkedid']] = 'NONE'
                                    if settings.DEBUG:
                                        print("DEBUG: RECORD FILE NOT FOUND")
                                    else:
                                        continue
                            else:
                                file_id[result['result']['Linkedid']] = 'MISSED'
                                if settings.DEBUG:
                                    print("DEBUG: MISSED CALL, NO FILE UPLOADS NEEDED")
                                else:
                                    continue

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

                        if settings.DEBUG:
                            print("DEBUG: API RESPONSE -- " + str(api_create_object.content))
                        else:
                            continue

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

                            record_name[result['result']['Linkedid']] = datetime.datetime.now().strftime(
                                "%Y-%m-%d-%H:%M") \
                                                                        + "-" \
                                                                        + str(result['result']['CallerIDNum']) + "-" \
                                                                        + str(
                                client_number[result['result']['Linkedid']]) \
                                                                        + '.wav'
                            if settings.DEBUG:
                                print('DEBUG: OUTGOING CALL STARTED WITH VALUES: \nCLIENT NUM: '
                                      + client_number[result['result']['Linkedid']] + "\nRECORD NAME: "
                                      + record_name[result['result']['Linkedid']])

                if (result['result']['Linkedid'] in outgoing_calls) is True \
                        and (result['result']['Linkedid'] in incoming_calls) is False:

                    if ('DialBegin' in result['result']['Event']) is False:

                        if result['result']['Exten'] != 'h' and \
                                ('Hangup' in result['result'].values()) is False and \
                                ('QueueMemberStatus' in result['result'].values()) is False:

                            timestamp_outgoing_events = datetime.datetime.fromtimestamp(
                                float(result['result']['Timestamp'])) \
                                .strftime("%H:%M:%S")
                            event_timestamp[result['result']['Linkedid']] = datetime.datetime.fromtimestamp(
                                int(str(result['result']['Timestamp'].split('.')[0])) -
                                start_timestamp[result['result']['Linkedid']]).strftime("%M:%S")

                            if 'DialState' in result['result']['Event']:
                                event_name[result['result']['Linkedid']] = 'Попытка звонка на номер ' \
                                                                           + client_number[result['result']['Linkedid']]
                                if result['result']['ChannelStateDesc'] == 'PROGRESS':
                                    dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                                elif result['result']['ChannelStateDesc'] == 'CONGESTION':
                                    dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                                else:
                                    dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                            elif 'BridgeEnter' in result['result']['Event'] and result['result']['Priority']:
                                event_name[result['result']['Linkedid']] = 'Разговор с абонентом ' \
                                                                           + client_number[result['result']['Linkedid']]
                                dial_status[result['result']['Linkedid']] = 'Звонок в процессе'
                            elif 'MusicOnHoldStart' in result['result']['Event']:
                                event_name[result['result']['Linkedid']] = 'Звонок переведён'
                                dial_status[result['result']['Linkedid']] = 'Звонок на удержании'
                            else:
                                event_name[result['result']['Linkedid']] = 'Попытка звонка на номер ' \
                                                                           + client_number[result['result']['Linkedid']]
                                dial_status[result['result']['Linkedid']] = 'Ожидание соединения'
                                if settings.DEBUG:
                                    print("DEBUG: UNKNOWN STATUS >> DEFAULT USED: " + str(result))
                                else:
                                    continue

                            outgoing_calls[result['result']['Linkedid']] += "/event/" \
                                                                            + str(
                                event_name[result['result']['Linkedid']]) \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/status/" \
                                                                            + dial_status[result['result']['Linkedid']] \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/time/" \
                                                                            + event_timestamp[
                                                                                result['result']['Linkedid']] \
                                                                            + " ///DELIMITER/// "
                        else:

                            employers = settings.get_employers_list()
                            if settings.DEBUG:
                                print("DEBUG: EMPLOYERS LIST: " + str(employers))
                            else:
                                continue

                            timestamp_outgoing_finished = datetime.datetime.fromtimestamp(
                                float(result['result']['Timestamp'])) \
                                .strftime("%H:%M:%S")
                            end_timestamp[result['result']['Linkedid']] = datetime.datetime.fromtimestamp(
                                int(str(result['result']['Timestamp']).split('.')[0]) -
                                start_timestamp[result['result']['Linkedid']]).strftime("%M:%S")

                            outgoing_calls[result['result']['Linkedid']] += "/event/" + "Звонок завершён" \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/status/" + "Конец звонка" \
                                                                            + " ///DELIMITER/// " \
                                                                            + "/time/" \
                                                                            + end_timestamp[
                                                                                result['result']['Linkedid']]

                            if len(str(result['result']['CallerIDNum'])) <= 3 or \
                                    len(str(result['result']['ConnectedLineNum'])) <= 3:
                                for number in employers:
                                    if str(number['number']) == str(result['result']['CallerIDNum']):
                                        operator[result['result']['Linkedid']] = [result['result']['CallerIDNum'],
                                                                                  number['name']]
                                        if settings.DEBUG:
                                            print("DEBUG: OPERATOR: " + str(operator[result['result']['Linkedid']]))
                                        else:
                                            continue
                                        break
                                    if str(number['number']) == str(result['result']['ConnectedLineNum']):
                                        operator[result['result']['Linkedid']] = [result['result']['ConnectedLineNum'],
                                                                                  number['name']]
                                        if settings.DEBUG:
                                            print("DEBUG: OPERATOR: " + str(operator[result['result']['Linkedid']]))
                                        else:
                                            continue
                                        break
                            else:
                                operator[result['result']['Linkedid']] = [result['result']['ConnectedLineNum'], '']

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

                            os.system('ls /home/fishhead/asterisk/records/ >> /dev/null')
                            if result['result']['Linkedid'] in record_name:
                                if 'Разговор' in outgoing_calls[result['result']['Linkedid']]:
                                    if os.path.isfile('/home/fishhead/asterisk/records/' + str(
                                            record_name[result['result']['Linkedid']])):
                                        record[result['result']['Linkedid']] = {"file": open(
                                            '/home/fishhead/asterisk/records/' + str(
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
                                            print("DEBUG: FILE CREATE -- " + str(api_upload_file.content))
                                        else:
                                            continue
                                    else:
                                        file_id[result['result']['Linkedid']] = 'NONE'
                                        if settings.DEBUG:
                                            print("DEBUG: RECORD FILE NOT FOUND")
                                        else:
                                            continue
                                else:
                                    file_id[result['result']['Linkedid']] = 'NOANSWER'
                                    if settings.DEBUG:
                                        print("DEBUG: DID NOT GET ANSWER, NO RECORD FILE NEEDED")
                                    else:
                                        continue

                            if ('NONE' in file_id[result['result']['Linkedid']]) is False \
                                    and ('NOANSWER' in file_id[result['result']['Linkedid']]) is False:
                                payload[result['result']['Linkedid']] = {"context": {
                                    "status_zvonka": [{"code": "otvechen_1", "name": "📤Отвечен"}],
                                    "type": [{"code": "iskhodyashii", "name": "Исходящий"}],
                                    "__name": str(client_number[result['result']['Linkedid']]),
                                    "nomer_operatora": str(operator[result['result']['Linkedid']][0]),
                                    "poslednii_operator": operator[result['result']['Linkedid']][1],
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
                                    "call_logs":
                                        {
                                            "rows": rows
                                        }
                                }
                                }

                            if settings.DEBUG:
                                print("DEBUG: PAYLOAD CONTEXT: " + str(payload[result['result']['Linkedid']]))
                            else:
                                continue
                            api_create_object = requests.post(settings.elma_settings['link'] + 'pub/v1/app/'
                                                              + settings.elma_settings['namespace'] + '/'
                                                              + settings.elma_settings['outgoing_calls'] + '/create',
                                                              data=json.dumps(payload[result['result']['Linkedid']]),
                                                              headers={
                                                                  'X-Token': settings.elma_settings['token'],
                                                              })

                            if settings.DEBUG:
                                print("DEBUG: API RESPONSE -- " + str(api_create_object.content))
                            else:
                                continue

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

        except Exception as exception:
            if settings.DEBUG:
                print("DEBUG: ERROR -- " + str(exception))
                pass
            else:
                pass
        except json.decoder.JSONDecodeError as json_error:
            if settings.DEBUG:
                print("DEBUG: JSON DECODER ERROR, ARGS: \n ERROR NAME: " + str(json_error)
                      + "\nLINE: " + str(event_string))
                pass
            else:
                pass

        current_string = ''
