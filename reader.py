import time;
import json;
import os;

KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

def read_line(file):

    for line in file:
        return line;


def read_events(file_path):

    stat = os.stat(file_path);

    print('Reading network events log file. Size : %.3f GB  Path : %s'%( stat.st_size / GIGA_BYTE, file_path));

    with open(file_path, 'r') as file:

        constants = json.loads(read_line(file).strip(',\n') + '}')['constants'];
        print(json.dumps(constants, indent = 3));

        constants['logEventPhaseMap'] = {constants['logEventPhase'][c] : c  for c in constants['logEventPhase']};

        constants['logSourceTypeMap'] = {constants['logSourceType'][c] : c  for c in constants['logSourceType']};

        constants['logEventTypesMap'] = {constants['logEventTypes'][c] : c  for c in constants['logEventTypes']};

        read_line(file);

        n_events = 0;

        for event in file:

            if 'params' not in event:
                continue;

            event = json.loads(s = event.strip(']}') + '}' if event[-2: ] == ']}' else event.strip(',\n'))
            
            if 'params' not in event or event['params'] == {}:
                continue;

            event['source']['type'] = constants['logSourceTypeMap'][event['source']['type']]

            if 'HTTP' in event['source']['type'] or 'URL' in event['source']['type']:

                event['source']['start_time'] = ((constants['timeTickOffset'] + int(event['source']['start_time']))) - 10800;
                event['time'] = ((constants['timeTickOffset'] + int(event['time']))) - 10800;
                event['phase'] = constants['logEventPhaseMap'][event['phase']];
                event['type']  = constants['logEventTypesMap'][event['type']];

                if 'source_dependency' in event['params']:
                    event['params']['source_dependency']['type'] = constants['logSourceTypeMap'][event['params']['source_dependency']['type']];
                    pass;

                yield event;

                n_events += 1;

                if n_events%100 == 0:
                    print('Read %d Events'%n_events);
                    pass;

                elif n_events > 10000000:
                    return;

def create_dir(path):

    levels = path.split('/');

    for level in range(2, len(levels) + 1):

        path = '/'.join(levels[:level]);

        if os.path.exists(path) == False:

            print(level,' Created %s Directory...'%(path));
            os.mkdir(path);
            pass;



def read(file_path):

    sources = dict();

    endpoints = dict();


    for event in read_events(file_path):

        if event['source']['id'] not in sources:

            if 'source_dependency' not in event['params']:

                if 'url' in event['params']:

                    sources[event['source']['id']] = event['params']['url'];

                    if event['params']['url'] not in endpoints:

                        endpoints[event['params']['url']] = {
                            'events' : list()
                        }

                else:

                    print(event);
                    continue;


            elif event['params']['source_dependency']['id'] in sources:
                sources[event['source']['id']] = sources[event['params']['source_dependency']['id']];
                pass;

            else:

                print('SOURCE', event);
                continue;

        endpoints[sources[event['source']['id']]]['events'].append(event);


def save(sources):

    for source in sources.values():

        source['dir'] = './logs/%s/%s'%(event['source']['type'], event['params']['url'].replace(':/','').split('?')[0].split('#')[0]);

        if os.path.exists(source['dir']) == False:
            create_dir(path = source['dir']);
            pass

        with open('%s/%s.json'%(source['dir'], source['name']), mode = 'w') as file:
            json.dump(source['events'], file, indent = 3)
            pass;


def read_test():

    read('C://Users/Tony/Desktop/network_log.json');
    pass;

read_test();