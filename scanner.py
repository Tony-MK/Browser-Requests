from datetime import datetime;
import glob
import re;
import time;
import json;
import os

from numpy import source;

KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

BATCH_SIZE = MEGA_BYTE * 96;

TIME_ZONE = 10800 * int(10 ** 3);

def scan(file_path):


    with open(file_path, "r") as file:

        lines = file.read(BATCH_SIZE).split(",\n");
        file.seek(file.tell() - len(lines[-1]));

        del lines[-1];
        
        try:

            constants =  json.loads(lines[0].strip(",\n") + "}")["constants"];
            pass;

        except json.JSONDecodeError as e:
            print(e.__str__());
            print('Failed to decode contants json line');
            return

        del lines[0];

        constants["timeTickOffset"] = int(constants["timeTickOffset"]) - TIME_ZONE;

        constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]};

        constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]};

        constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]};

        yield constants;

        lines[0] = lines[0].split("\n")[-1];

        while True:

            print("Scan network events log file. Scanned : %.3f GB / %.3f GB  (%.3f%s) Path : %s"%( file.tell() / GIGA_BYTE, os.stat(file_path).st_size / GIGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path));

            for line in lines:

                try:
                    
                    yield json.loads(line.strip(",\n"));

                except json.decoder.JSONDecodeError as e:
                    print(line);
                    raise e;

            while round(file.tell() / os.stat(file_path).st_size, 2) == 1:

                if os.stat(file_path).st_atime + 300 > datetime.now().timestamp():
                    return;

                print("Awaiting log change....", end = "\r")
                time.sleep(.3);
                pass;

            lines = file.read(BATCH_SIZE).split(",\n");

            file.seek(file.tell() - len(lines[-1]));
            del lines[-1];
        
def read(file_path, hosts):
    

    print("Reading " + str(file_path)  + ".....\nLast Update : " + str(datetime.now().timestamp() - os.stat(file_path).st_atime) + " ago ");

    reader = scan(file_path);
    
    try:
        
        constants = next(reader);

        sources = dict();

        for event in reader:

            if "params" not in event:
                event["params"] = {};

            elif "source_dependency" in event["params"]:
                event["params"]["source_dependency"]["type"] = constants["logSourceTypeMap"][event["params"]["source_dependency"]["type"]]

            event["source"]["start_time"] = constants["timeTickOffset"] + int(event["source"]["start_time"])
            event["source"]["type"] = constants["logSourceTypeMap"][event["source"]["type"]]
            event["time"] = constants["timeTickOffset"] + int(event["time"])
            event["phase"] = constants["logEventPhaseMap"][event["phase"]]
            event["type"]  = constants["logEventTypesMap"][event["type"]]

            if event["source"]["id"] in sources:
                sources[event["source"]["id"]].events.append(event);

            elif "source_dependency" in event["params"] and event["params"]["source_dependency"]["id"] in sources:

                sources[event["source"]["id"]] = sources[event["params"]["source_dependency"]["id"]];
                sources[event["source"]["id"]].events.append(event);

            elif "url" in event["params"]:

                url = event["params"]["url"]

                scheme, url = url[:url.find("://")], url[url.find("://") + 3:];

                host_name, url = url[:url.find("/")],  url[url.find("/") + 1:];

                if host_name not in hosts:
                    continue;

                path = hosts[host_name].find(url.split('/'));

                if path == None:
                    continue;

                if path.events == 0:

                    print("Starting New %d Path Sources %d, %s %s"%(hosts[host_name].get_size(), len(sources), scheme,  path.url));
                    pass;
                    
                else:

                    for e in path.events:
                        if e['source']['id'] in sources:
                            del sources[e['source']['id']]

                path.events = [event];
                sources[event["source"]["id"]] = path;
                pass;

            yield event
    
    except StopIteration as e:
        print(e);
        


def scan_dir(dir_path, hosts):

    file_paths = list()

    for file_num, file_path in  enumerate(glob.glob(dir_path + "/*.json")):

        if datetime.now().timestamp() -  os.stat(file_path).st_atime < 3600 * 24:

            print(end = "%d) Skipping Network Log File : "%(file_num));
            print(file_path + ".....\nLast Update : " + str(datetime.now().timestamp() - os.stat(file_path).st_atime) + " ago ");
        
        elif os.stat(file_path).st_size / KILO_BYTE < 1:
            print(end = "%d) Skipping Network Log File : "%(file_num));
            print(file_path + "......\nSize of log file is not valid %d Bytes"%file_path);
        
        else:

            file_paths.append(file_path);
            pass;
    
    file_paths.sort(key = lambda file_path : os.stat(file_path).st_atime);
    
    for file_path in file_paths:
        read(file_path = file_path);
             
