import json;
import os;

KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

def read_line(file):

    for line in file:
        return line.strip(',\n') + '}';


def get_events(file):


    with open(file_path, 'r') as file:

        constants = json.loads(read_line(file));

        if constants == None:
            return;

        LOG_PHASES = {constants['constants']['logEventPhase'][c] : c  for c in constants['constants']['logEventPhase']};

        SOURCE_TYPES = {constants['constants']['logSourceType'][c] : c  for c in constants['constants']['logSourceType']};

        EVENT_TYPES = {constants['constants']['logEventTypes'][c] : c  for c in constants['constants']['logEventTypes']};

        start_time = constants['constants']['timeTickOffset'];

        index = 0;

        read_line(file);

        for event in file

            event = json.loads(line = event.strip(']}') + '}' if event[-2: ] == ']}' else event.strip(',\n') + '}')

            add_keys(event)
           
            if event['source']['type'] == 1:


                event['phase'] = LOG_PHASES[event['phase']];
                event['source']['type'] = SOURCE_TYPES[event['source']['type']]
                event['type']  = EVENT_TYPES[event['type']];
                event['source']['start_time'] = ((start_time + int(event['source']['start_time']))) - 10800;
                event['time'] = ((start_time + int(event['time']))) - 10800;

                if 'params' in event:
                
                    if 'source_dependency' in event['params']:
                        event['params']['source_dependency']['type'] = SOURCE_TYPES[event['params']['source_dependency']['type']];
                        pass;

                else:

                    event['params'] = {};
                    pass;



def read(file_path):

    stat = os.stat(file_path);

    print('Reading network log file ( %.3f MB)  %s ....'%( stat.st_size / GIGA_BYTE, file_path));

    for event in read_file(file):

        index += 1;

        if index < 10000000:

            



def read_test():
    for event in read('C://Users/Tony/Desktop/network_log.json'):
        print(event);

read_test();