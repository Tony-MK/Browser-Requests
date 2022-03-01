from datetime import datetime;
import glob
import re;
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
            
def create_dir(path):

    levels = path.split('/');

    for depth in range(2, len(levels) + 1):

        path = '/'.join(depth[:depth]);

        if os.path.exists(path) == False:

            print(depth,' Created %s Directory...'%(path));
            os.mkdir(path);
            pass;



def read(file_path):

    reader = scan(file_path);

    constants = next(reader);

    for event in reader:

        if 'params' in event:

            if 'source_dependency' in event["params"]:
                event["params"]['source_dependency']['type'] = constants['logSourceTypeMap'][event["params"]['source_dependency']['type']]

            event['source']['start_time'] = constants['timeTickOffset'] + int(event['source']['start_time'])
            event['source']['type'] = constants['logSourceTypeMap'][event['source']['type']]
            event['time'] = constants['timeTickOffset'] + int(event['time'])
            event['phase'] = constants['logEventPhaseMap'][event['phase']]
            event['type']  = constants['logEventTypesMap'][event['type']];
            yield event;

            

       

def scan_dir(dir_path, hosts):

    sources = dict();

    urls = dict();

    paths = dict();

    file_paths = glob.glob(dir_path + '/*.json');

    print('Scanning ' + str(len(file_paths))  + ' Network Logs | ' + dir_path );
    
    print('Reading ' + str(file_paths[-1])  + '......')

    for event in read(file_paths[-1]):

        
        if event['source']['id'] in sources:
            sources[event['source']['id']].events.append(event);
            pass;

        elif 'source_dependency' in event['params'] and event['params']['source_dependency']['id'] in sources:

            sources[event['source']['id']] = sources[event['params']['source_dependency']['id']];
            sources[event['source']['id']].events.append(event);

        elif 'url' in event['params'] and 'pinnacle.com' in event['params']['url']:        

            path = hosts[0].add_path('://'.join(event['params']['url'].split('://')[1:]).split("/"));
            if path != None:
                print('Starting New %d Path Sources %d'%(len(hosts[0].paths), len(sources)));
                path.events = [event];
                sources[event['source']['id']] = path;                

