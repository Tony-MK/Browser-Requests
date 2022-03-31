from asyncio import constants
import base64
from datetime import datetime
import asyncio
import gzip
import glob
import json
import os

KILO_BYTE = 2 ** 10;
MEGA_BYTE = 2 ** 20;
GIGA_BYTE = 2 ** 30;

CACHE_DURATION = 3600 * 3;

BATCH_SIZE = MEGA_BYTE * 256;

TIME_ZONE = 10800 * int(10 ** 3);

INGNORE_EVENT_TYPES = [
	"URL_REQUEST_START_JOB",
	"REQUEST_ALIVE",
	"CREATED_BY",
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
    #"HTTP2_SESSION_RECV_DATA",
    "HTTP2_SESSION_RECV_SETTING",
    "HTTP_STREAM_JOB_CONTROLLER_BOUND" ,
    "HTTP_STREAM_REQUEST_BOUND_TO_JOB",
    "HTTP2_SESSION_POOL_FOUND_EXISTING_SESSION",
    "HTTP_STREAM_REQUEST_STARTED_JOB",
    "HTTP_STREAM_JOB_WAITING",
    "HTTP_STREAM_JOB_CONTROLLER_PROXY_SERVER_RESOLVED",
];

file_stats = lambda file, file_path : "%.3f MB / %.3f MB  (%.3f%) Path : %s | Last Update : %.3f seconds ago"%(file.tell() / MEGA_BYTE, os.stat(file_path).st_size / MEGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 , "%", file_path.split("\\")[1], datetime.now().timestamp() - os.stat(file_path).st_mtime)


def decode_headers(headers):

	if len(headers) == 1:
		headers = headers[0];
		pass;

	if headers[0].find("HTTP") != -1:
		headers[0] = "version: " + headers[0];
	
	return { header.split(': ')[0] : header.split(': ')[1] for header in headers };



def get_file_paths(dir_path):

	file_paths = list();

	for file_num, file_path in  enumerate(glob.glob(dir_path + "/*.json")):

		if os.stat(file_path).st_size == 0:
			os.remove(file_path);

		elif datetime.now().timestamp() - os.stat(file_path).st_mtime < CACHE_DURATION:
			file_paths.append(file_path);

	file_paths.sort(key = lambda file_path : os.stat(file_path).st_mtime);
	return file_paths;

def decode_event(event: dict, constants: dict) -> dict:

	if "params" not in event:
		event["params"] = {};

	elif "source_dependency" in event["params"]:
		event["params"]["source_dependency"]["type"] = constants["logSourceTypeMap"][event["params"]["source_dependency"]["type"]]

	event["source"]["start_time"] = constants["timeTickOffset"] + int(event["source"]["start_time"])
	event["source"]["type"] = constants["logSourceTypeMap"][event["source"]["type"]]
	event["time"] = constants["timeTickOffset"] + int(event["time"])
	event["phase"] = constants["logEventPhaseMap"][event["phase"]]
	event["type"]  = constants["logEventTypesMap"][event["type"]];
	return event;




def print_data(data, n = 100):
	n /= 2;
	return data[:n] + "\n" + "".join(["...."] * 25) + "\n" + data[-n:] if len(data) > n else data;


def handle_url_request(url_req):
		
	req, resp = url_req["request"], url_req["response"];

	data = base64.b64decode(resp["data"].encode('UTF-8')).decode('UTF-8', 'ignore');

	print("\n" + "".join(["-"] * 133) + "\nResource : " + str(url_req["path"].resource));
	print("REQUEST - url : %s Headers : %d Data : %d bytes"%(url_req["path"], len(req["headers"]), len(req["data"])));
	print("RESPONSE - Headers : %d Data : %d bytes"%( len(resp["headers"]), len(resp["data"])));
	
	if len(resp["data"]) > 0:

		print_data(data);

		data = url_req["path"].endpoints[req["method"]]['decoder'](data);
		print(data);

		getattr(url_req["path"].resource, url_req["path"].endpoints[req["method"]]["handler"])(data);
	
	print("SUCCESSFULLY HANDLED URL REQUEST\n" + ''.join(['-'] * 133))

def read_constants(file):

	constants = file.readline();

	constants = json.loads(constants.strip(",\n") + "}" )["constants"];

	constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]};

	constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]};

	constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]};

	constants["timeTickOffset"] = int(constants["timeTickOffset"]) - TIME_ZONE;

	return constants;

async def read(file_path, Hosts, wait = False) -> None:

	remove = not wait;

	with open(file_path, "r") as file:
		
		constants = read_constants(file);

		file.readline();file.readline();
		

		nth_byte, running, sources = file.tell(), True, dict();

		while running:
			
			if nth_byte == os.stat(file_path).st_size:

				if wait == False:
					print("Stopped : %s"%(file_stats(file, file_path)));
					break;
				
				while nth_byte == os.stat(file_path).st_size:
					print("Waiting : %s"%(file_stats(file, file_path)));
					await asyncio.sleep(.3);
			
			file.seek(nth_byte, os.SEEK_SET);
			buff = file.read(BATCH_SIZE);
			nth_byte += len(buff);

			for event in buff.split(",\n"):
	
				try:
					event = json.loads(event);
				except json.decoder.JSONDecodeError as e:
					
					running = False;
					if len(event) < 3:
						continue;
					
					try:
						event = json.loads(event[:-3]);
						pass;
					
					except json.JSONDecodeError as e:
						print('Event', event[:200], e)
						continue;
				
				event = decode_event(event, constants);
				
				source_id, source_type = event["source"]["id"], event["source"]["type"]; del event["source"];
				event_type = event["type"]; del event["type"];
				params = event["params"]; del event["params"];
				phase = event["phase"]; del event["phase"];
				_ = event["time"]; del event["time"];
				assert len(event) == 0, str(event.keys());

				if source_type in ["SOCKET", "DISK_CACHE_ENTRY", "NETWORK_QUALITY_ESTIMATOR", "NONE", "PAC_FILE_DECIDER", "CERT_VERIFIER_JOB"]:
					continue;

				if source_id in sources:
					pass;

				elif "source_dependency" in params and params["source_dependency"]["id"] in sources:
					sources[source_id] = sources[params["source_dependency"]["id"]];
					sources[source_id]["sources"].add(source_id)
		
				elif "url" in params and "method" in params:
					
					url = params["url"];

					method = params["method"].lower()

					scheme, url = url[:url.find("://") + 3], url[url.find("://") + 3:];

					host, path = url[:url.find("/")],  url[url.find("/") + 1:];

					if host not in Hosts:
						continue;
					
					remove = False;

					path = Hosts[host].find(path.split("/"));

					if path == None :
						continue;

					elif path.resource == None:
						#print("NO RESOURCE FOUND URL : %s%s"%(scheme, url))
						continue;

					path.methods[params["method"]] = {
						"request" :  {"method" : method, "headers" : "", "data" : "" },
						"response" : { "headers" : "", "data" : "" },
						"source_id" : source_id,
						"sources" : set([source_id]),
						"path" : path,
					};

					sources[source_id] = path.methods[params["method"]];
					print("%d) %s - %s%s"%(len(sources), event_type, scheme, url));

				else:

					#print(event["source"]["type"], "Source Id Not Found : ", event["type"], event.keys(), event["params"].keys(), end = "\n");
					continue;
				

				if len(params) > 0 and event_type not in INGNORE_EVENT_TYPES :

					req, res = sources[source_id]["request"], sources[source_id]["response"];

					if event_type in ["HTTP2_SESSION_SEND_HEADERS", "CORS_REQUEST", "URL_REQUEST"] : # "HTTP_TRANSACTION_HTTP2_SEND_REQUEST_HEADERS"]:

						if "headers" in params:
							req["headers"] = params["headers"];
						else:
							print("Headers not found %s from source type %s with parameters (%s)"%(event_type, source_type, ",".join(params.keys())));
					
					elif event_type in ["HTTP2_SESSION_RECV_HEADERS"] : #"HTTP_TRANSACTION_READ_RESPONSE_HEADERS"]:
						res["headers"] = params["headers"];
					
					elif event_type in ["URL_REQUEST_JOB_FILTERED_BYTES_READ" ]:
						res["data"] += params["bytes"];

						if phase == "PHASE_END":

							handle_url_request(sources[source_id]);
							pass;

					else:
						print("Unkwown event type %s from source type %s with parameters (%s)"%(event_type, source_type, ",".join(params.keys())));
						pass;


				if phase == "PHASE_END":
					
					try: del sources[source_id];

					except KeyError as e: print("Source Id:", e);
		
	try:
		
		if remove == True and wait == False:
			print("DELETING ... %s"%(file_path.split("\\")[-1]));
			#os.remove(path=file_path);
			
	except PermissionError as e:
		print(e);
		pass;
		
				
