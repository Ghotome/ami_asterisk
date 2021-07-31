import datetime
import json
import os
import re
import telnetlib

import settings

telnet_session = telnetlib.Telnet(settings.connection['address'], settings.connection['port'])
username = "Username: " + settings.login_data['username']
secret = "Secret: " + settings.login_data['secret']
telnet_session.write("Action:login".encode('ascii') + b"\n"
                     + username.encode('ascii') + b"\n"
                     + secret.encode('ascii') + b"\n\n")

current_string = ''
parsed_string = {}
event_dict = {}


# noinspection PyGlobalUndefined


def incoming_call_logging(result):
    global file
    pid = 1
    caller_number = ''
    print("DEBUG: ALL EVENTS LOG -- " + str(result['result']))
    if ('Answer' in result['result'].values()) is True:
        pid = os.fork()
        caller_number = str(result['result']['CallerIDNum'])

    print("DEBUG: PID -- " + str(pid))
    if pid == 0:
        print("DEBUG: CALLER NUMBER -- " + caller_number)
        if ('CallerIDNum' in result['result']) is True:
            if ((result['result']['CallerIDNum'] == caller_number or
                 result['result']['CallerIDNum'] == "+" + str(caller_number)) and
                    (result['result']['Event'] == 'Newstate' or
                     result['result']['Event'] == 'DialState' or
                     result['result']['Event'] == 'Newexten' or
                     result['result']['Event'] == 'BridgeEnter' or
                     result['result']['Event'] == 'Hangup')):
                if ('Answer' in result['result'].values()) is True:
                    print("DEBUG: PASSED CHECK - ANSWER")
                    print("DEBUG: RESULT -- " + str(result['result']))
                    file = open('/home/fishhead/Desktop/test/' + result['result']['CallerIDNum'] + "_"
                                + str(
                        datetime.datetime.utcfromtimestamp(float(result['result']['Timestamp']))),
                                'a')
                    file.write(str(result['result']) + "\n\n")

                elif ('Hangup' in result['result'].values()) is True:
                    print("DEBUG: PASSED CHECK - HANGUP")
                    print("DEBUG: RESULT -- " + str(result['result']))
                    file.write(str(result['result']) + "\n\n")

                else:
                    print('DEBUG: PASSED CHECK - ANOTHER')
                    print("DEBUG: RESULT -- " + str(result['result']))
                    file.write(str(result['result']) + "\n\n")
    else:
        pass


while True:
    event_string = ''
    elements_string = ''
    count = 0
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
            count += 1
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
            parsed_string = json.loads(event_string)
            print("DEBUG: CURRENT PARSED LINE -- " + str(parsed_string))

        except json.decoder.JSONDecodeError:
            print("JSON Decode Error, разобраться позже")

        incoming_call_logging(parsed_string)
        current_string = ''
