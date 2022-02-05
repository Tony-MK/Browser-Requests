from datetime import datetime;
import json;
import glob;
import os;


BIT = 1;
KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

PARAMS = [
    'initiator', 
    'url', 
    'method', 
    'headers', 
    'priority', 
    'source_dependency', 
    'address_list', 
    'phase', 
    'canonical_name', 
    'local_address',
    'time',
    'pac_string',
    'is_preconnect'
];

SOURCE_TYPES = {
    1 : ['URL_REQUEST' , handle_url_request_events,
            [
                "URL_REQUEST_DELEGATE_CERTIFICATE_REQUESTED", # 108,
                "URL_REQUEST_DELEGATE_RECEIVED_REDIRECT", # 109,
                "URL_REQUEST_DELEGATE_RESPONSE_STARTED", # 110,
                "URL_REQUEST_DELEGATE_SSL_CERTIFICATE_ERROR", # 111,
                "URL_REQUEST_FAKE_RESPONSE_HEADERS_CREATED", # 117,
                "URL_REQUEST_FILTERS_SET", # 118,
                "URL_REQUEST_JOB_BYTES_READ", # 113,
                "URL_REQUEST_JOB_FILTERED_BYTES_READ", # 114,
                "URL_REQUEST_REDIRECTED", # 104,
                "URL_REQUEST_REDIRECT_JOB", # 116,
                "URL_REQUEST_SET_PRIORITY", # 115,
                "URL_REQUEST_START_JOB", # 103,
            ]
        ],

    8 : 'SOCKET',
    9 : 'HTTP2_SESSION',
    23 : 'HTTP_STREAM_JOB_CONTROLLER',
    15 : 'HTTP_STREAM_JOB',

};

from functools import wraps;


def handle():

    def deco():

        @wraps
        def wrap(**args, **kwrags):

            return func(**args);

        return wrap

    return deco

def handle_url_request_event(event):

    print(event)





source_handlers = {
    'URL_REQUEST' : handle_url_request(),
    
}




def readLine(file):
    for line in file:
        return line

def decodeLine(line):
    
    try:

        event =  json.loads(line);
        pass

    except json.decoder.JSONDecodeError as e:
        print(e.__str__() + '\n' + 'Line: ', line);
        pass;

    else:

        if type(event) == dict:
            return event;

        raise Exception('Failed to decode json line : ' + line);


SOURCES = {

};

def to_string(event):
    return json.dumps(event, indent = 3) + '\n';

def save_event(event):

    if event['source']['id'] not in SOURCES:

        SOURCES[event['source']['id']] = { 
            'key' : ' file_name '.join(list(map(lambda k : event['params'][k], ['url', 'method'])));
            'start_time' : event['source']['start_time'],
            'end_time' : event['time'],
            'duration' : event['time'] - 
            'type' : event['source']['id'],
            'events' : {
                event['type'] : [event],
            },
        };


    elif event['type'] not in SOURCES[event['source']['id']]['events']:

        SOURCES[event['source']['id']]['events'][event['type']] = [event];
        pass;

    else:

        SOURCES[event['source']['id']]['events'][event['type']].append(event);
        pass;


    SOURCES[event['source']['id']]['end_time'] = event['time'];
    SOURCES[event['source']['id']]['duration'] = SOURCES[event['source']['id']]['start_time'] - SOURCES[event['source']['id']]['end_time']

    pass;


EVENT_KEYS = dict();


def open_log_file(file_path):

    stat = os.stat(file_path);

    print('Scanning network log file ( %.3f MB)  %s ....'%( stat.st_size / MEGA_BYTE, file_path));

    with open(file_path, 'r') as file:

        constants = json.loads(readLine(file).strip(',\n') + '}');

        if constants == None:
            return;

        LOG_PHASES = {constants['constants']['logEventPhase'][c] : c  for c in constants['constants']['logEventPhase']};

        SOURCE_TYPES = {constants['constants']['logSourceType'][c] : c  for c in constants['constants']['logSourceType']};

        EVENT_TYPES = {constants['constants']['logEventTypes'][c] : c  for c in constants['constants']['logEventTypes']};

        start_time = constants['constants']['timeTickOffset'] ;

        index = 0;

        readLine(file);

        for event in file:

            if index > 10000000:
                break;

            index += 1;

            event = decodeLine(line = event.strip(']}') + '}' if event[-2: ] == ']}' else event.strip(',\n'))

            add_keys(event)
           
            if event['source']['type'] == 1 and 'params' in event:

                if 'source_dependency' in event['params']:
                    event['params']['source_dependency']['type'] = SOURCE_TYPES[event['params']['source_dependency']['type']];
                    pass;

                event['phase'] = LOG_PHASES[event['phase']];
                event['source']['type'] = SOURCE_TYPES[event['source']['type']]
                event['type']  = EVENT_TYPES[event['type']];
                event['source']['start_time'] = ((start_time + int(event['source']['start_time']))) - 10800;
                event['time'] = ((start_time + int(event['time']))) - 10800;
                save_event(event);

import hashlib;
import base64;


def get(source_index, key, value):
    for event_type in SOURCES[source_index]['events']:
        for event in SOURCES[source_index]['events'][event_type]:
            if key in event['params'] and value in event['params'][key]:
                return SOURCES[source_index]['events'];

for source_index in SOURCES:

    event = get(source_index, key = 'url', value = 'pinnacle');
    if event != None:
        print(json.dumps(event, indent = 3));

def isHostScanComplete(endpoints):
    for endpoint in endpoints:
        if len(endpoints[endpoint]['methods']) == 0:
            return endpoint

def scanHostsRequests(file_path):

    sources = {};

    for event in read_log_events(file_path, source_types = [1], event_types = [2, 100, 110, 111, 112, 166, 169, 164, 448]):

        try:

            if 'url' in event['params'] and 'method' in event['params']:
                print(event);
                pass;

            elif event['source']['id'] not in sources:
                pass;
            
            elif 'headers' in event['params']:

                if 'HTTP' in event['params']['headers'][0]:
                    event['params']['headers'][0] = 'version: ' + event['params']['headers'][0]

                    sources[event['source']['id']]['response']  = {

                        'headers': { header.split(': ')[0] : header.split(': ')[1] for header in event['params']['headers'] },
                        'timestamp' : event['timestamp'],
                    }

                else:

                    sources[event['source']['id']]['request']  = {
                        'headers': { header.split(': ')[0] : header.split(': ')[1] for header in event['params']['headers'] },
                        'timestamp' : event['timestamp'],
                    }

            #elif 'bytes' in event['params']:#event['type'] == 'URL_REQUEST_DELEGATE_RESPONSE_STARTED' or event['type'] == 'URL_REQUEST_JOB_BYTES_READ':
            #    sources[event['source']['id']]['response']['duration']  = event['timestamp'] - sources[event['source']['id']]['response']['timestamp'] ;
            #    sources[event['source']['id']]['response']['size']  += event['params']['byte_count'];
            #    sources[event['source']['id']]['response']['body']  += event['params']['bytes'];
            #    pass;


            #elif event['type'] == 'URL_REQUEST_SET_PRIORITY':

            #    sources[event['source']['id']]['priority'] = event['params']['priority']
            #    pass;

        except Exception as e:
            print(e);
            print(event);
            pass

    return isHostScanComplete(endpoints);


def save_request(profile, request):

    with open(parameters.PROFILE_DIR + profile + '/' + request['path'] + '.json', 'w') as file:
        json.dump(request, file, indent = 3);
        pass;
