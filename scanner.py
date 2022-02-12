from datetime import datetime;
import glob;
import time;
import json;
import os;



KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

BATCH_SIZE = MEGA_BYTE * 96;

TIME_ZONE = 10800 * int(10 ** 3);



def save(sources):

    for source in sources.values():

        source['dir'] = './logs/%s/%s'%(event['source']['type'], event['params']['url'].replace(':/','').split('?')[0].split('#')[0]);

        if os.path.exists(source['dir']) == False:
            create_dir(path = source['dir']);
            pass

        with open('%s/%s.json'%(source['dir'], source['name']), mode = 'w') as file:
            json.dump(source['events'], file, indent = 3)
            pass;


def scan(file_path):

    with open(file_path, 'r') as file:

        lines = file.read(BATCH_SIZE).split(',\n');
        file.seek(file.tell() - len(lines[-1]));
        del lines[-1];
            
        constants =  json.loads(lines[0].strip(',\n') + '}')['constants'];

        del lines[0];

        constants['timeTickOffset'] = int(constants['timeTickOffset']) - TIME_ZONE;

        constants['logEventPhaseMap'] = {constants['logEventPhase'][c] : c  for c in constants['logEventPhase']};

        constants['logSourceTypeMap'] = {constants['logSourceType'][c] : c  for c in constants['logSourceType']};

        constants['logEventTypesMap'] = {constants['logEventTypes'][c] : c  for c in constants['logEventTypes']};

        yield constants;

        lines[0] = lines[0].split('\n')[-1];

        while True:

            print('Scan network events log file. Scanned : %.3f GB / %.3f GB  (%.3f%s) Path : %s'%( file.tell() / GIGA_BYTE, os.stat(file_path).st_size / GIGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , '%', file_path));

            for line in lines:

                try:
                    
                    yield json.loads(line.strip(',\n'));

                except json.decoder.JSONDecodeError as e:
                    print(line);
                    raise e;


            while round(file.tell() / os.stat(file_path).st_size, 3) == 1:
                print('Awaiting log change....', end = '\r')
                time.sleep(.3);
                pass;

            lines = file.read(BATCH_SIZE).split(',\n');
            file.seek(file.tell() - len(lines[-1]));
            del lines[-1];
            

def read_line(reader):
    for line in reader:
        return line;
            

def create_dir(path):

    levels = path.split('/');

    for level in range(2, len(levels) + 1):

        path = '/'.join(levels[:level]);

        if os.path.exists(path) == False:

            print(level,' Created %s Directory...'%(path));
            os.mkdir(path);
            pass;



def read(file_path):

    reader = scan(file_path);

    constants = next(reader);

    for event in reader:

        if 'params' in event:

            if 'source_dependency' in event:
                event['source_dependency']['type'] = constants['logSourceTypeMap'][event['source_dependency']['type']]

            event['source']['type'] = constants['logSourceTypeMap'][event['source']['type']]
            event['source']['start_time'] = constants['timeTickOffset'] + int(event['source']['start_time']);
            event['time'] = constants['timeTickOffset'] + int(event['time'])
            event['phase'] = constants['logEventPhaseMap'][event['phase']];
            event['type']  = constants['logEventTypesMap'][event['type']];
            yield event;

       

def scan_hosts(dir_path, hosts):

    sources = dict();

    urls = dict();

    file_paths = glob.glob(dir_path + '/*.json');

    print('Scanning ' + str(len(file_paths))  + ' Network Logs | ' + dir_path + '\nReading ' + str(file_paths[-1])  + '......')

    for event in read(file_paths[-1]):

        if 'HTTP' not in event['source']['type'] and 'URL' not in event['source']['type']:
            continue;

        elif event['source']['id'] in sources:
            urls[sources[event['source']['id']]]['events'][-1].append(event);
            continue;

        elif 'source_dependency' in event['params'] and event['params']['source_dependency']['id'] in sources:

            sources[event['source']['id']] = sources[event['params']['source_dependency']['id']];

            urls[sources[event['source']['id']]]['events'][-1].append(event);
            continue;

        elif 'url' not in event['params']:
            continue;

        for host in hosts:

            if host not in event['params']['url']:
                continue

            for route in hosts[host]:

                if route['cache'] < datetime.utcnow().timestamp() - event['time']:
                    continue;

                elif route['route'] in event['params']['url']:

                    sources[event['source']['id']] = event['params']['url'];

                    if event['params']['url'] in urls:

                        urls[event['params']['url']]['events'].append([event]);
                        print(len(urls[sources[event['source']['id']]]['events']), ' New Endpoint Request: ' + sources[event['source']['id']]);
                    
                    else:

                        urls[event['params']['url']] = {
                            'events' : [[event]],
                        };

                        print(len(urls), ' New Endpoint: ' + sources[event['source']['id']]);








hosts = {

    'pinnacle.com' : [ 
        {'route' : '/0.1/matchups' , 'cache' :  TIME_ZONE},
        {'route' : '/0.1/leagues' , 'cache' :  TIME_ZONE},
        {'route' : '/0.1/status' , 'cache' :  TIME_ZONE},
    ],

};


scan_hosts(dir_path = 'C://Users/Tony/Desktop/BetBot/Profiles/Logs/Network', hosts = hosts);