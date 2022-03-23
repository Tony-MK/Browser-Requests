import asyncio
from datetime import datetime;
import glob
import re;
import time;
import json;
import os
 
KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

CACHE_DURATION = 300;

BATCH_SIZE = MEGA_BYTE * 96;

TIME_ZONE = 10800 * int(10 ** 3);
    
    
def get_file_paths(dir_path):

    file_paths = list();

    for file_num, file_path in  enumerate(glob.glob(dir_path + "/*.json")):

        if datetime.now().timestamp() - os.stat(file_path).st_mtime > CACHE_DURATION:
            print(str(file_num) + ") Updated : " + str(int(datetime.now().timestamp() - os.stat(file_path).st_mtime)) + " seconds ago. Skipping  : %s...."%(file_path));

        elif os.stat(file_path).st_size < 128:
            print("%d) Skipping Network Log File : %s...."%(file_num, file_path));
            print("Size of log file is not valid : " + str(os.stat(file_path).st_size) + " Bytes\n");
        
        else:
            file_paths.append(file_path);

    file_paths.sort(key = lambda file_path : os.stat(file_path).st_mtime);
    return file_paths;

async def read(file_path, Hosts):
                
    with open(file_path, "r") as file:

        lines = file.read(BATCH_SIZE).split(",\n");

        try:

            constants = json.loads(lines[0].strip(",\n") + "}")["constants"];
            
        except Exception as e:
            print(lines);
            raise e
        
        del lines[0];

        constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]};

        constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]};

        constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]};

        constants["timeTickOffset"] = int(constants["timeTickOffset"]) - TIME_ZONE;

        lines[0] = lines[0].split("\n")[-1];

        sources = dict();

        while True:
            
            for line in lines[:-1]:

                try:

                    event = json.loads(line);
                    pass;

                except json.decoder.JSONDecodeError as e:
                    print(line);
                    print(e);
                
                else:

                    if "params" not in event:
                        event["params"] = {};

                    elif "source_dependency" in event["params"]:
                        event["params"]["source_dependency"]["type"] = constants["logSourceTypeMap"][event["params"]["source_dependency"]["type"]]

                    event["source"]["start_time"] = constants["timeTickOffset"] + int(event["source"]["start_time"])
                    event["source"]["type"] = constants["logSourceTypeMap"][event["source"]["type"]]
                    event["time"] = constants["timeTickOffset"] + int(event["time"])
                    event["phase"] = constants["logEventPhaseMap"][event["phase"]]
                    event["type"]  = constants["logEventTypesMap"][event["type"]];
                    
                    if event["source"]["id"] in sources:
                        sources[event["source"]["id"]].events.append(event);

                    elif "source_dependency" in event["params"] and event["params"]["source_dependency"]["id"] in sources:

                        sources[event["source"]["id"]] = sources[event["params"]["source_dependency"]["id"]];
                        sources[event["source"]["id"]].events.append(event);

                    elif "url" in event["params"]:

                        url = event["params"]["url"]

                        scheme, url = url[:url.find("://")], url[url.find("://") + 3:];

                        host_name, url = url[:url.find("/")],  url[url.find("/") + 1:];

                        if host_name not in Hosts:
                            #print(scheme, host_name, url);
                            continue;

                        path = Hosts[host_name].find(url.split('/'));

                        if path == None:
                            continue;

                        for e in path.events:
                            if e['source']['id'] in sources:
                                del sources[e['source']['id']]

                        path.events = [event];
                        sources[event["source"]["id"]] = path;
                        print("Starting New %d Path Sources %d, %s %s"%(path.get_size(), len(sources), scheme,  path.url));
                        pass;
                    
            print("Scanned : %.3f GB / %.3f GB  (%.3f%s) Path : %s"%( file.tell() / GIGA_BYTE, os.stat(file_path).st_size / GIGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path) + " | Last Update : " + str(round(datetime.now().timestamp() - os.stat(file_path).st_mtime)) + " seconds ago");

            while file.tell() == os.stat(file_path).st_size:
                
                print("Scanned : %.3f GB / %.3f GB  (%.3f%s) Path : %s"%( file.tell() / GIGA_BYTE, os.stat(file_path).st_size / GIGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path) + " | Last Update : " + str(round(datetime.now().timestamp() - os.stat(file_path).st_mtime)) + " seconds ago")
                
                if datetime.now().timestamp() - os.stat(file_path).st_mtime > CACHE_DURATION:
                    print("Finished");
                    return;
                
                print("Awating new network events...");
                await asyncio.sleep(3);
            
            file.seek(file.tell() - len(lines[-1]));
            lines = file.read(BATCH_SIZE).split(",\n");