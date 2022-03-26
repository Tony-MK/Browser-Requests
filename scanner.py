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

	def get_path(event):

		url = event["params"]["url"];

		scheme, url = url[:url.find("://")], url[url.find("://") + 3:];

		host, path = url[:url.find("/")],  url[url.find("/") + 1:];

		if host in Hosts:

			path = Hosts[host].find(path.split("/"));

			if path != None:

				if "method" in event["params"]:

					path.methods[event["params"]["method"]] = {
						"response" : "",
					}

					sources[event["source"]["id"]] = path.methods[event["params"]["method"]];
					print("%d Starting New Events Sequence %s: %s"%(len(sources), event["type"], path.url));
					return path;

				elif "original_url" in event["params"]:
					print("METHOD NOT FOUND - EVENT TYPE ", event["type"], "KEYS : " , ",".join(list(event["params"].keys())));

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
				

				try:

					if 'google' in event or 'beacons' in event:
						continue;
					
					
					event = json.loads(event);
				except json.decoder.JSONDecodeError as e:

					try:

						if len(event) < 3:
							continue;

						event = json.loads(event[:-3]);
						running = False;
					except json.decoder.JSONDecodeError as e: 
						print(event, e);
						continue;
				
				event = decode_event(event);
				
				print(event)

				if event["source"]["id"] in sources:
					pass;

				elif "source_dependency" in event["params"] and event["params"]["source_dependency"]["id"] in sources:
					sources[event["source"]["id"]] = sources[event["params"]["source_dependency"]["id"]];
				
				elif "url" not in event["params"]:
					#print("EVENT URL NOT FOUND : ", event["type"], event.keys(), event["params"].keys(), end = "\r");
					continue;
				

				if get_path(event) == None:
					continue;

				endpoint = sources[event["source"]["id"]];
				print(endpoint)

				if "bytes" in event["params"]:
					endpoint["response"] += event["params"]["bytes"];
					print("Processed %s (%d) |  Response : %d  (%d) "%(event["type"], len(sources), len(endpoint["response"], event["params"]["bytes_count"])));
				else:
					print("Processed %s (%d) |  Response : %d "%(event["type"], len(sources),  len(endpoint["response"])));

				if event["phase"] == "PHASE_END":
					del sources[event["source"]["id"]];
	
		print("Stopped : %s"%(file_stats(file, file_path)));

					

				
