import asyncio
from datetime import datetime;
import glob
import time;
import json;
import os
from urllib.parse import non_hierarchical

KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

CACHE_DURATION = 3600 * 72;

BATCH_SIZE = MEGA_BYTE * 96;

TIME_ZONE = 10800 * int(10 ** 3);

file_stats = lambda file, file_path : "%.3f MB / %.3f MB  (%.3f%s) Path : %s | Last Update : %s seconds ago"%(file.tell() / MEGA_BYTE, os.stat(file_path).st_size / MEGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path, datetime.now().timestamp() - os.stat(file_path).st_mtime)


def get_file_paths(dir_path):

	file_paths = list();

	for file_num, file_path in  enumerate(glob.glob(dir_path + "/*.json")):

		if datetime.now().timestamp() - os.stat(file_path).st_mtime < CACHE_DURATION:
			file_paths.append(file_path);

	file_paths.sort(key = lambda file_path : os.stat(file_path).st_mtime);
	return file_paths;

async def read(file_path, Hosts, wait = False):

	def decode_event(event):

		if "params" not in event:
			event["params"] = dict();

		elif "source_dependency" in event["params"]:
			event["params"]["source_dependency"]["type"] = constants["logSourceTypeMap"][event["params"]["source_dependency"]["type"]]

		event["source"]["start_time"] = constants["timeTickOffset"] + int(event["source"]["start_time"])
		event["source"]["type"] = constants["logSourceTypeMap"][event["source"]["type"]]
		event["time"] = constants["timeTickOffset"] + int(event["time"])
		event["phase"] = constants["logEventPhaseMap"][event["phase"]]
		event["type"]  = constants["logEventTypesMap"][event["type"]];
		return event;


	with open(file_path, "r") as file:

		constants = file.readline();

		try:
			constants = json.loads(constants.strip(",\n") + "}")["constants"];
		except Exception as e:
			print(constants, e.__str__());
			return;
		
		constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]};

		constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]};

		constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]};

		constants["timeTickOffset"] = int(constants["timeTickOffset"]) - TIME_ZONE;

		file.readline();
		file.readline().split("\n")[-1];

		sources = dict();

		running = True;

		while running:
			
			if file.tell() == os.stat(file_path).st_size and wait == False:
				break;
			
			else:

				while file.tell() == os.stat(file_path).st_size:
					print("Scanned : %s"%(file_stats(file, file_path)));
					await asyncio.sleep(3);
			
			for event in file.read(BATCH_SIZE).split(",\n"):
				
				if "params" not in event or 'google' in event or 'beacons' in event:
					continue;
				
				try:
					event = json.loads(event);
				except json.decoder.JSONDecodeError as e:
					
					running = False;
					if len(event) < 3:
						continue;
						
					event = json.loads(event[:-3]);
					pass;
				
				event = decode_event(event);

				if event["source"]['type'] in ["SOCKET", "DISK_CACHE_ENTRY", "NETWORK_QUALITY_ESTIMATOR", "NONE", "PAC_FILE_DECIDER", "CERT_VERIFIER_JOB"]:
					continue;
				
				elif event["source"]["id"] in sources:
					pass;

				elif "source_dependency" in event["params"] and event["params"]["source_dependency"]["id"] in sources:
					sources[event["source"]["id"]] = sources[event["params"]["source_dependency"]["id"]];
					sources[event["source"]["id"]]["sources"].add(event["source"]["id"])
		
				elif "url" in event["params"] and "method" in event["params"]:
					
					url = event["params"]["url"];

					scheme, url = url[:url.find("://")], url[url.find("://") + 3:];

					host, path = url[:url.find("/")],  url[url.find("/") + 1:];

					if host not in Hosts:
						continue;

					path = Hosts[host].find(path.split("/"));

					if path == None:
						#print("NO PATH FOUND : %s"%(url))
						continue;

					path.methods[event["params"]["method"]] = {
						"request" :  {"headers" : "", "data" : "" },
						"response" : { "headers" : "", "data" : "" },
						"source_id" : event["source"]["id"],
						"sources" : set([event["source"]["id"]]),
					}
					sources[event["source"]["id"]] = path.methods[event["params"]["method"]];
					print("%d Starting New Events Sequence %s: %s"%(len(sources), event["type"], path.url));
					pass;

				else:
					
					#if event["type"] != "COOKIE_STORE_COOKIE_ADDED":
						#print(event["source"]["type"], "TYPE NOT FOUND : ", event["type"], event.keys(), event["params"].keys(), end = "\n");
					continue;
				

				endpoint = sources[event["source"]["id"]];

				params = event["params"];
				
				if event["type"] == "HTTP2_SESSION_SEND_HEADERS":
	
					endpoint["request"]["headers"] = params["headers"];
				
				elif event["type"] == "HTTP2_SESSION_RECV_HEADERS":
	
					endpoint["response"]["headers"] = params["headers"];
				
				elif event["type"] in ["URL_REQUEST_JOB_BYTES_READ", "URL_REQUEST_JOB_FILTERED_BYTES_READ"] :

					endpoint["response"]["bytes"] = params["bytes"];
					pass;

				else:
					
					if "bytes" in params:
						print("response", event["type"]);
						continue;
					print("NO UNKWOWN EVENT TYPE : ", event["type"], event["params"].keys());

				#if "bytes" in event["params"]:

				#	endpoint["response"]["data"] += params["bytes"];
				#	print("Processed %s (%d) |  Response : %d  (%d) "%(event["type"], len(sources), len(endpoint["resp"], params["byte_count"])));
				
				

				

				if event["phase"] == "PHASE_END":
					del sources[event["source"]["id"]];
	
		print("Stopped : %s"%(file_stats(file, file_path)));

					

				
