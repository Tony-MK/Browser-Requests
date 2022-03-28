from datetime import datetime
import asyncio
import glob
import json
import os

KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

CACHE_DURATION = 3600 * 24;

BATCH_SIZE = MEGA_BYTE * 256;

TIME_ZONE = 10800 * int(10 ** 3);

INGNORE_EVENT_TYPES = [
    "COOKIE_INCLUSION_STATUS""CREATED_BY",
    "CHECK_CORS_PREFLIGHT_REQUIRED",
    "CHECK_CORS_PREFLIGHT_CACHE",
    "COMPUTED_PRIVACY_MODE",
    "COOKIE_INCLUSION_STATUS" ,
    "CORS_PREFLIGHT_RESULT",
    "CORS_PREFLIGHT_CACHED_RESULT",
    "DELEGATE_INFO",
    "HTTP_STREAM_JOB_BOUND_TO_REQUEST",
    "HTTP2_SESSION_UPDATE_RECV_WINDOW",
    "HTTP2_STREAM_UPDATE_RECV_WINDOW",
    "HTTP2_SESSION_SEND_WINDOW_UPDATE",
    "HTTP2_SESSION_RECV_DATA",
    "HTTP2_SESSION_RECV_SETTING",
    "HTTP_STREAM_JOB_CONTROLLER_BOUND" ,
    "HTTP_STREAM_REQUEST_BOUND_TO_JOB",
    "HTTP2_SESSION_POOL_FOUND_EXISTING_SESSION",
    "HTTP_STREAM_REQUEST_STARTED_JOB",
    "HTTP_STREAM_JOB_WAITING",
    "HTTP_STREAM_JOB_CONTROLLER_PROXY_SERVER_RESOLVED",
];

file_stats = lambda file, file_path : "%.3f MB / %.3f MB  (%.3f%s) Path : %s | Last Update : %s seconds ago"%(file.tell() / MEGA_BYTE, os.stat(file_path).st_size / MEGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path.split("\\")[0], datetime.now().timestamp() - os.stat(file_path).st_mtime)


def get_file_paths(dir_path):

	file_paths = list();

	for file_num, file_path in  enumerate(glob.glob(dir_path + "/*.json")):

		if datetime.now().timestamp() - os.stat(file_path).st_mtime < CACHE_DURATION:
			file_paths.append(file_path);

	file_paths.sort(key = lambda file_path : os.stat(file_path).st_mtime);
	return file_paths;

def decode_event(event: dict, constants: dict) -> dict:

	if "source_dependency" in event["params"]:
		event["params"]["source_dependency"]["type"] = constants["logSourceTypeMap"][event["params"]["source_dependency"]["type"]]

	event["source"]["start_time"] = constants["timeTickOffset"] + int(event["source"]["start_time"])
	event["source"]["type"] = constants["logSourceTypeMap"][event["source"]["type"]]
	event["time"] = constants["timeTickOffset"] + int(event["time"])
	event["phase"] = constants["logEventPhaseMap"][event["phase"]]
	event["type"]  = constants["logEventTypesMap"][event["type"]];
	return event;

def handle_response(resp):

	resp['headers'][0] = 'version: ' + resp['headers'][0];

	headers = { header.split(': ')[0] : header.split(': ')[1] for header in resp['headers'] };

	print(json.dumps(headers, indent=True));
	print(resp["data"][:100])
	pass;


async def read(file_path, Hosts, wait = False) -> None:

	remove = not wait;

	with open(file_path, "r") as file:

		constants = file.readline();

		try:

			constants = json.loads(constants.strip(",\n") + "}")["constants"];

			constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]};

			constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]};

			constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]};

			constants["timeTickOffset"] = int(constants["timeTickOffset"]) - TIME_ZONE;
			
		except Exception as e:
			print(constants, e.__str__());
			return

		file.readline()
		file.readline();

		sources = dict()

		running = True;

		current_byte, buff = file.tell(), None;

		while running:
			
			del buff;

			if current_byte == os.stat(file_path).st_size:

				if wait == False:
					print("Stopped : %s"%(file_stats(file, file_path)));
					break;
				
				while current_byte == os.stat(file_path).st_size:
					print("Waiting : %s"%(file_stats(file, file_path)));
					await asyncio.sleep(3);
			
			file.seek(current_byte, os.SEEK_SET);
			buff = file.read(BATCH_SIZE);
			current_byte += len(buff);

			for event in buff.split(",\n"):
				
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
				
				event = decode_event(event, constants);

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
						continue;
					
					elif path.resource == None:
						continue;
				
					remove = False;
					
					path.methods[event["params"]["method"]] = {
						"request" :  {"headers" : "", "data" : "" },
						"response" : { "headers" : "", "data" : "" },
						"source_id" : event["source"]["id"],
						"sources" : set([event["source"]["id"]]),
						"path" : path,
					};

					sources[event["source"]["id"]] = path.methods[event["params"]["method"]];
					#print("%d Starting New Events Sequence %s: %s"%(len(sources), event["type"], path.url));

				else:

					#print(event["source"]["type"], "TYPE NOT FOUND : ", event["type"], event.keys(), event["params"].keys(), end = "\n");
					continue;
				
				params = event["params"];
				endpoint = sources[event["source"]["id"]];

				if event["type"] in ["HTTP2_SESSION_SEND_HEADERS", "HTTP_TRANSACTION_HTTP2_SEND_REQUEST_HEADERS"]:
	
					endpoint["request"]["headers"] = params["headers"];
				
				elif event["type"] in ["HTTP2_SESSION_RECV_HEADERS", "HTTP_TRANSACTION_READ_RESPONSE_HEADERS"]:
	
					endpoint["response"]["headers"] = params["headers"];
				
				elif event["type"] in ["URL_REQUEST_JOB_BYTES_READ", "URL_REQUEST_JOB_FILTERED_BYTES_READ"] :
					endpoint["response"]["data"] += params["bytes"];

				elif event["type"] == "CORS_REQUEST":
					endpoint["request"]["headers"] = params["headers"];

				elif event["type"] in INGNORE_EVENT_TYPES:
					pass;
				
				else:
					#print("NO UNKWOWN EVENT TYPE : ", event["type"], event);
					pass;
				
				if event["phase"] == "PHASE_END":
					print(sources[event["source"]["id"]]["path"].resource);
					print(sources[event["source"]["id"]]["source_id"], sources[event["source"]["id"]]["sources"]);
					print(len(sources[event["source"]["id"]]["request"]["headers"]), len(sources[event["source"]["id"]]["response"]["headers"]));
					print(len(sources[event["source"]["id"]]["request"]["data"]), len(sources[event["source"]["id"]]["response"]["data"]), end = "\n\n");

					if  len(sources[event["source"]["id"]]["response"]["headers"]) > 1:
						handle_response(resp = sources[event["source"]["id"]]["response"])
					
					#sources[event["source"]["id"]]["sources"].remove(event["source"]["id"]);
					
					#if sources[event["source"]["id"]]["source_id"] == event["source"]["id"] :
						
					#del sources[event["source"]["id"]];
		
	try:
		
		if remove == True and wait == False:
			print("Deleting %s"%(file_path.split("\\")[0]));
			os.remove(path=file_path);
			
	except PermissionError as e:
		print(e);
		pass;
		
		

					

				
