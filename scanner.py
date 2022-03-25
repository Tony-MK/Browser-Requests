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

CACHE_DURATION = 180000;

BATCH_SIZE = MEGA_BYTE * 96;

TIME_ZONE = 10800 * int(10 ** 3);
    
    
def get_file_paths(dir_path):

    file_paths = list();

    for file_num, file_path in  enumerate(glob.glob(dir_path + "/*.json")):

        if datetime.now().timestamp() - os.stat(file_path).st_mtime < CACHE_DURATION:
            file_paths.append(file_path);

        #print(str(file_num) + ") Updated : " + str(int(datetime.now().timestamp() - os.stat(file_path).st_mtime)) + " seconds ago. Skipping  : %s...."%(file_path));

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
                    print(line, e);
                
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

                        sources[event["source"]["id"]]["events"].append(event);

                        if "bytes" in event["params"]:
                            sources[event["source"]["id"]]["response"] += event["params"] + "bytes";
                            pass;

                        if event["phase"] == "PHASE_END":
                            print(len(sources), event["type"] + " Ended ", len(sources[event["source"]["id"]].events), path.url);
                            print(sources[event["source"]["id"]]["response"])
                            del sources[event["source"]["id"]]                        

                    elif "source_dependency" in event["params"] and event["params"]["source_dependency"]["id"] in sources:

                        sources[event["source"]["id"]] = sources[event["params"]["source_dependency"]["id"]];
                        sources[event["source"]["id"]]["events"].append(event);

                        if "bytes" in event["params"]:
                            sources[event["source"]["id"]]["response"] += event["params"] + "bytes";
                            pass;

                        if event["phase"] == "PHASE_END":
                            print(len(sources), event["type"] + " Ended ", len(sources[event["source"]["id"]].events), path.url);
                            print(sources[event["source"]["id"]]["response"]);
                            del sources[event["source"]["id"]]                        
                        

                    elif "url" in event["params"]:

                        url = event["params"]["url"];

                        scheme, url = url[:url.find("://")], url[url.find("://") + 3:];

                        host, url = url[:url.find("/")],  url[url.find("/") + 1:];

                        if host in Hosts:

                            path = Hosts[host].find(url.split("/"));
                            if path != None:
                                
                                if "method" in event["params"]:

                                    path.methods[event["params"]["method"]] = {
                                        "response" : "",
                                        "events" : [event]
                                    }

                                    sources[event["source"]["id"]] = path.methods[event["params"]["method"]];
                                
                                    print("Starting New Events Sequence %d, %s://%s"%(len(sources), scheme,  path.url));
                                    pass;

                                elif "original_url" in event["params"]:
                                    print(event["params"]["url"],  event["original_url"], event["params"].keys());
                                
                                else:

                                    print(event["params"]);

                                
                                
                    

            while file.tell() == os.stat(file_path).st_size:
                
                print(end= "Scanned : %.3f GB / %.3f GB  (%.3f%s) Path : %s | Last Update : %s seconds ago"%(file.tell() / GIGA_BYTE, os.stat(file_path).st_size / GIGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path, datetime.now().timestamp() - os.stat(file_path).st_mtime));
                
                if datetime.now().timestamp() - os.stat(file_path).st_mtime > CACHE_DURATION:
                    print("Network Events Finished...");
                    return;
                
                print("Awating new network events...");
                await asyncio.sleep(3);
            
            print(end="Reading | %.3f GB / %.3f GB  (%.3f%s) Path : %s | Last Update : %s seconds ago"%(file.tell() / GIGA_BYTE, os.stat(file_path).st_size / GIGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path, datetime.now().timestamp() - os.stat(file_path).st_mtime));

            file.seek(file.tell() - len(lines[-1]));
            lines = file.read(BATCH_SIZE).split(",\n");