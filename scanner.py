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

BATCH_SIZE = MEGA_BYTE * 64;

TIME_ZONE = 10800 * int(10 ** 3);

INGNORE_EVENT_TYPES = [
	"REQUEST_ALIVE",
	"CREATED_BY",
    "CHECK_CORS_PREFLIGHT_REQUIRED",
    "CHECK_CORS_PREFLIGHT_CACHE",
    "COMPUTED_PRIVACY_MODE",
    "COOKIE_INCLUSION_STATUS" ,
    "CORS_PREFLIGHT_RESULT",
    "CORS_PREFLIGHT_CACHED_RESULT",
    "DELEGATE_INFO",
	"NETWORK_DELEGATE_BEFORE_START_TRANSACTION",
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

file_stats = lambda file, file_path, nth_byte : "%.3f MB / %.3f MB  (%.3f%s) Path : %s | Last Update : %.3f seconds ago"%(nth_byte / MEGA_BYTE, os.stat(file_path).st_size / MEGA_BYTE, nth_byte / os.stat(file_path).st_size * 100 , "%", file_path.split("\\")[1], datetime.now().timestamp() - os.stat(file_path).st_mtime)


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
			os.delete(file_path);

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
	n = int(n/2);
	return data[:n] + "\n" + "".join(["...."] * 25) + "\n" + data[-n:] if len(data) > n else data;


def handle_url_request(url_req):
		
	req, resp = url_req["request"], url_req["response"];

	print("\n" + "".join(["-"] * 133) + "\nResource : " + str(url_req["path"].resource));
	print("REQUEST %s - %s Headers : %d Data : %d bytes"%(req["method"],url_req["path"].url, len(req["headers"]), len(req["data"])));
	print("RESPONSE - Headers : %d Data : %d bytes"%( len(resp["headers"]), len(resp["data"])));
	
	if len(resp["data"])  == 0:
		return;
		
	data = base64.b64decode(resp["data"]).decode('UTF-8', 'ignore');
	print_data(data);

	try:

		handler = getattr(url_req["path"].resource, url_req["path"].endpoints[req["method"]]["handler"]);
		print('HANDLING URL REQUEST....')
		handler(url_req["path"].endpoints[req["method"]]['decoder'](data));
		print("URL REQUEST HANDLE SUCCEDED " + ''.join(['-'] * 133), end = "\n\n");
		pass;
		
	except json.JSONDecodeError as e:
		print("URL REQUEST HANDLE FAILED %s"%(e) + ''.join(['-'] * 133), end = "\n\n");
	
	

def read_constants(file):

	constants = file.readline();

	constants = json.loads(constants.strip(",\n") + "}" )["constants"];

	constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]};

	constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]};

	constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]};

	constants["timeTickOffset"] = int(constants["timeTickOffset"]) - TIME_ZONE;

	return constants;

async def read_log(file_path, profile) -> None:
	
	delete = False;

	with open(file_path, "r") as file:
		
		constants = read_constants(file);

		file.readline();
		file.readline();
		
		nth_byte, running, sources = file.tell(), True, dict();

		while running:
			p = 0;
			if nth_byte == os.stat(file_path).st_size:

				if datetime.now().timestamp() - os.stat(file_path).st_mtime > CACHE_DURATION:
					print("Stopped : %s"%(file_stats(file, file_path, nth_byte)));
					break;
				
				while nth_byte == os.stat(file_path).st_size:
					p += 1;
					await asyncio.sleep(.3);
					if p%33 == 0:
						print("Waiting : %s"%(file_stats(file, file_path, nth_byte)));
					
			
			print("Reading : %s "%(file_stats(file, file_path, nth_byte)));
			file.seek(nth_byte, os.SEEK_SET);
			buff = file.read(BATCH_SIZE);
			nth_byte += len(buff);

			for event in buff.split(",\n"):
				
				if event == "":
					if datetime.now().timestamp() - os.stat(file_path).st_mtime > CACHE_DURATION:
						running = False;
					continue;

				try:
					event = json.loads(event);
					running = True;
				except json.decoder.JSONDecodeError as e:
					
					try:

						event = json.loads(event[:-3]);
						running = True;
					except json.JSONDecodeError as e:
						print('Event', event[:200], e);
						continue;

				event = decode_event(event, constants);
				
				source_id, source_type = event["source"]["id"], event["source"]["type"]; del event["source"];
				event_type = event["type"]; del event["type"];
				params = event["params"]; del event["params"];
				phase = event["phase"]; del event["phase"];
				_ = event["time"]; del event["time"];
				assert len(event) == 0, str(event.keys());
				del event;

				if source_type in ["SOCKET", "DISK_CACHE_ENTRY", "NETWORK_QUALITY_ESTIMATOR", "NONE", "PAC_FILE_DECIDER", "CERT_VERIFIER_JOB"]:
					continue;

				elif source_id in sources:
					pass;

				elif "source_dependency" in params and params["source_dependency"]["id"] in sources:
					sources[source_id] = sources[params["source_dependency"]["id"]];
					sources[source_id]["sources"].add(source_id)
		
				elif "url" in params and "method" in params:
					
					url = params["url"];

					method = params["method"].lower()

					scheme, url = url[:url.find("://") + 3], url[url.find("://") + 3:];

					host, _path = url[:url.find('/')],  url[url.find('/') + 1:].split("?")[0];

					if host not in profile.Hosts:
						continue;
					
					#print(profile.Hosts[host], len(profile.Hosts[host].routes), _path.split("/"));

					delete = False;
					path = profile.Hosts[host].find(_path.split("/"));

					if path == None :
						print("NO RESOURCE PATH : %s %s%s/%s"%(params["method"], scheme, host,_path))
						continue;

					elif path.resource == None:
						print("NO RESOURCE FOUND URL : %s %s%s"%(params["method"], scheme, url))
						continue;

					path.methods[params["method"]] = {
						"request" :  {"method" : method, "headers" : "", "data" : "" , "encoded" : ""},
						"response" : { "headers" : "", "data" : "", "encoded" : "" },
						"source_id" : source_id,
						"sources" : set([source_id]),
						"path" : path,
					};

					sources[source_id] = path.methods[params["method"]];
					print("%d) %s - %s %s%s"%(len(sources), event_type, params["method"], scheme, url));
					pass;

				else:

					#print(event["source"]["type"], "Source Id Not Found : ", event["type"], event.keys(), event["params"].keys(), end = "\n");
					continue;
				
				req, res = sources[source_id]["request"], sources[source_id]["response"];

				if event_type in ["HTTP2_SESSION_SEND_HEADERS", "CORS_REQUEST", "URL_REQUEST_START_JOB"] : # "HTTP_TRANSACTION_HTTP2_SEND_REQUEST_HEADERS"]:

					if "headers" in params:
						req["headers"] = params["headers"];
					else:
						print("Headers not found %s from source type %s with parameters (%s)"%(event_type, source_type, ",".join(params.keys())));
				
				elif event_type in ["HTTP2_SESSION_RECV_HEADERS", "HTTP_TRANSACTION_READ_RESPONSE_HEADERS"]:
					res["headers"] = params["headers"];
				
				elif event_type in ["URL_REQUEST_JOB_FILTERED_BYTES_READ"]:
					res["data"] += params["bytes"];
					

				elif event_type in ["HTTP2_SESSION_RECV_DATA"]:
					print("%s from source type %s with parameters (%s)"%(event_type, source_type, ",".join(params.keys())));
					print(params);

				elif event_type in ["URL_REQUEST_JOB_BYTES_READ"]:
					res["encoded"] +=  params["bytes"];
					
				elif len(params) > 0 and event_type not in INGNORE_EVENT_TYPES :
						print("Unkwown event type %s from source type %s with parameters (%s)"%(event_type, source_type, ",".join(params.keys())));
			

				if phase == "PHASE_END" :
					handle_url_request(sources[source_id]);
			
			del buff;
			pass;
		
	try:
		
		if delete == True:
			print("DELETING ... %s"%(file_path.split("\\")[-1]));
			#os.delete(path=file_path);
			
	except PermissionError as e:
		print(e);
		pass;
		
				
