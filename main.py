import datetime
import json
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
result = {}
event_dict = {}
incoming_calls = {}
outgoing_calls = {}
timestamp = ''

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

            result = json.loads(event_string)
            print("DEBUG: CURRENT LINE -- " + str(result['result']))

            # INCOMING CALLS

            if ('Answer' in result['result'].values()) is True:
                timestamp = datetime.datetime.fromtimestamp(float(result['result']['Timestamp'])) \
                    .strftime("%Y-%m-%d_%H:%M:%S")
                incoming_calls[result['result']['Channel']] = str(result['result']) + " ///DELIMITER/// "
                print('DEBUG: INCOMING CALL STARTED -- ' + str(incoming_calls[result['result']['Channel']]))

            if ('Channel' in result['result']) is True \
                    and not ('Answer' in result['result'].values()) is True \
                    and (result['result']['Channel'] in incoming_calls) is True:

                if ('Answer' in result['result'].values()) is False \
                        and ('Hangup' in result['result'].values()) is False \
                        and (result['result']['Channel'] in incoming_calls) is True:
                    print("DEBUG: INCOMING CALL - ANY EVENTS -- "
                          + str(incoming_calls[result['result']['Channel']]))
                    incoming_calls[result['result']['Channel']] += str(result['result']) + " ///DELIMITER/// "

                if ('Hangup' in result['result'].values()) is True:
                    if result['result']['ConnectedLineNum'] == '<unknown>' and \
                            result['result']['CallerIDNum'] != '<unknown>':
                        file = open('/home/fishhead/Desktop/test/INCOMING_'
                                    + result['result']['CallerIDNum'] + str(timestamp), 'a')
                        incoming_calls[result['result']['Channel']] += str(result['result']) + " ///DELIMITER/// "
                        print(
                            'DEBUG: INCOMING CALL FINISHED 1 -- ' + str(incoming_calls[result['result']['Channel']]))
                        file.write(incoming_calls[result['result']['Channel']].replace(' ///DELIMITER/// ', '\n\n'))
                        file.close()
                        incoming_calls.pop(result['result']['Channel'], None)

                    elif result['result']['ConnectedLineNum'] != '<unknown>' and \
                            result['result']['CallerIDNum'] == '<unknown>':
                        file = open('/home/fishhead/Desktop/test/INCOMING_'
                                    + result['result']['ConnectedLineNum'] + str(timestamp), 'a')
                        incoming_calls[result['result']['Channel']] += str(
                            result['result']) + " ///DELIMITER/// "
                        print(
                            'DEBUG: INCOMING CALL FINISHED 2 -- ' + str(
                                incoming_calls[result['result']['Channel']]))
                        file.write(
                            incoming_calls[result['result']['Channel']].replace(' ///DELIMITER/// ', '\n\n'))
                        file.close()
                        incoming_calls.pop(result['result']['Channel'], None)
                    else:
                        file = open('/home/fishhead/Desktop/test/INCOMING_'
                                    + result['result']['CallerIDNum'] + str(timestamp), 'a')
                        incoming_calls[result['result']['Channel']] += str(
                            result['result']) + " ///DELIMITER/// "
                        print(
                            'DEBUG: INCOMING CALL FINISHED 3 -- ' + str(
                                incoming_calls[result['result']['Channel']]))
                        file.write(
                            incoming_calls[result['result']['Channel']].replace(' ///DELIMITER/// ', '\n\n'))
                        file.close()
                        incoming_calls.pop(result['result']['Channel'], None)

            # OUTGOING CALLS


        except json.decoder.JSONDecodeError:
            print("JSON Decode Error")

        current_string = ''
