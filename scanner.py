from datetime import datetime
import base64
import asyncio
import glob
import json
import os

KILO_BYTE : int = 1024
MEGA_BYTE : int = 1024 ** 2;

SCREEN_WIDTH = 150;

DASH_LINE = ''.join(['-'] * SCREEN_WIDTH) + '\n';

CACHE_DURATION : int = 3600 / 3;

BATCH_SIZE : int = MEGA_BYTE * 32

UTC_DELTA : int = int(datetime.now().timestamp() - datetime.utcnow().timestamp()) * 1000
print("SYSTEM TIMEZONE DIFFERENCE : ", UTC_DELTA)

file_stats = lambda file, file_path : "%s (%d mins ago) %.1f/%.1f MB (%.2f%%)"%(file.name.split("\\")[-1], round(datetime.now().timestamp() - os.stat(file_path).st_mtime) * 60, file.tell() / MEGA_BYTE, os.stat(file_path).st_size / MEGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 )


def decode_headers(headers):

	if len(headers) == 1:
		headers = headers[0];
		pass;

	if headers[0].find("HTTP") != -1:
		headers[0] = "version: " + headers[0];
	
	return { header.split(': ')[0] : header.split(': ')[1] for header in headers };

def get_file_paths(dir_path : str, modified = CACHE_DURATION, latest = True) -> list:

	paths = glob.glob(dir_path + "/*.json");

	if len(paths) == 0:
		return list();
		
	paths.sort(key = lambda fp : os.stat(fp).st_mtime, reverse = True);

	file_paths = list();

	if latest == True:
		file_paths.append(paths[0]);
		del paths[0];

	start = datetime.now().timestamp() - CACHE_DURATION;

	for file_path in paths:

		if start > os.stat(file_path).st_mtime:
			break;

		file_paths.append(file_path);

	return file_paths;

def map_event(event: dict, constants: dict) -> dict:

	if "source" not in event:
		print(event, "\nNetwork Log event does not have source key")
		return;

	elif "params" not in event:
		event["params"] = {};

	elif "source_dependency" in event["params"]:
		event["params"]["source_dependency"]["type"] = constants["logSourceTypeMap"][event["params"]["source_dependency"]["type"]];
		event["params"]["source_dependency"]["id"] = int(event["params"]["source_dependency"]["id"]);


	event["source"]["start_time"] = constants["timeTickOffset"] + int(event["source"]["start_time"])
	event["source"]["type"] = constants["logSourceTypeMap"][event["source"]["type"]];
	event["source"]["id"] = int(event["source"]["id"]);

	event["time"] = constants["timeTickOffset"] + int(event["time"])
	event["phase"] = constants["logEventPhaseMap"][event["phase"]]
	event["type"]  = constants["logEventTypesMap"][event["type"]];
	return event;


def print_data(data : str, n = 100) -> None:
	n = int(n/2);
	return data[:n] + "\n" + "".join(["...."] * 25) + "\n" + data[-n:] if len(data) > n else data;


def handle_url_request(url_req : dict) -> None:
		
	try:

		req, resp = url_req["request"], url_req["response"];
		query = url_req["path"].endpoints[req["method"]];

		data = base64.b64decode(resp["data"]).decode('UTF-8', 'ignore')

		getattr(url_req["path"].resource, query["handler"])(query['decoder'](data));
		pass;
	
	except Exception as e:
		
		if "/b" in url_req["path"].url and "/w" not in url_req["path"].url:

			print(DASH_LINE + "%s %s\nHeaders : %d Data : %d"%(req["method"].upper(), url_req["path"].url, len(req["headers"]), len(req["data"])), end = ' | ');
			print("Encoded: %d Headers : %d Data : %d"%(len(resp["encoded"]), len(resp["headers"]), len(resp["data"])));
			print_data(resp["data"]);
			print("FAILED TO HANDLE RESPONSE %s"%(e));
			print(e.__traceback__.tb_frame.f_trace_lines)
			print(DASH_LINE);
	
def read_constants(file):

	constants = file.readline();

	constants = json.loads(constants.strip(",\n") + "}" )["constants"];

	constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]};

	constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]};

	constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]};

	constants["timeTickOffset"] = int(constants["timeTickOffset"]) - UTC_DELTA;

	return constants;

async def standby(nth_byte, file, file_path):

	p = 0;
	while nth_byte == os.stat(file_path).st_size:

		if p%33 == 0:
			print("STANDBY - Bytes : %.3f MB %s"%(nth_byte / MEGA_BYTE, file_stats(file, file_path)));

		await asyncio.sleep(3);
		p += 1;


async def read_log(file_path, profile) -> None:
	
	
	while MEGA_BYTE > os.stat(file_path).st_size:

		if datetime.now().timestamp() - os.stat(file_path).st_mtime > 300:
			print("SMALL LOG FILE : %d Bytes %s"%(os.stat(file_path).st_size, file_path));
			return;
		
		print("NEW LOG FILE : %d Bytes %s"%(os.stat(file_path).st_size, file_path));
		await asyncio.sleep(30);
		

	with open(file_path, "r") as file:
		
		try:

			constants, sources = read_constants(file), dict();

		except json.decoder.JSONDecodeError:
			print("\n\nCONSTANTS DECODE ERROR : %s\n\n"%(file_stats(file, file_path)));
			pass;

		else:
	
			file.readline();
			file.readline();
			
			nth_byte, n_bytes, nth_iteration, running, buff  = file.tell(), 0, 0, True, list();

			while running:

				del buff;

				nth_iteration += 1;

				await standby(file = file, file_path = file_path, nth_byte = nth_byte)

				nth_byte = nth_byte - n_bytes;
				file.seek(nth_byte, os.SEEK_SET);
				buff = file.read(BATCH_SIZE);
				nth_byte += len(buff);

				buff = buff.split(",\n")
				#n_bytes = len(buff[-1]);
				#del buff[-1];

				for event in buff:
					
					try:

						event = json.loads(event);
						running = True;

					except json.decoder.JSONDecodeError:

						try:

							if len(event) == 0:
								continue;

							elif event[0] != "{" or event[-1] != "}":
								#print("INVALID JSON STRING (%s bytes) : %s"%(len(event), event[:100]));
								running = True;
								continue;

							elif event[:-2] == '}]':
								event = json.loads(event[:-1]);
								running = False;
								pass;

							else:

								event = json.loads(event[:-3]);
								running = True;
								pass;

						except json.JSONDecodeError as e:
							print("EVENT DECODE ERROR - " + str(e) + '\n' + event, end = "\n\n");
							continue;

					event = map_event(event, constants);

					if event == None or event["source"]["type"] in ["SOCKET"]: #"DISK_CACHE_ENTRY", "NETWORK_QUALITY_ESTIMATOR", "NONE", "PAC_FILE_DECIDER", "CERT_VERIFIER_JOB":
						continue;

					source_id, source_type = event["source"]["id"], event["source"]["type"]; del event["source"];

					event_type = event["type"]; del event["type"];
					params = event["params"]; del event["params"];
					phase = event["phase"]; del event["phase"];
					_ = event["time"]; del event["time"];
					assert len(event) == 0, str(event.keys());
					del event;

					if source_id not in sources:

						if "source_dependency" in params and params["source_dependency"]["id"] in sources:
							sources[source_id] = sources[params["source_dependency"]["id"]];

							# Adding to sources set
							sources[source_id]["sources"].add(source_id)
						
						elif "url" not in params or "method" not in params:
							#print(event["source"]["type"], "Source Id Not Found : ", event["type"], event.keys(), event["params"].keys(), end = "\n");
							continue;

						else:

							url = params["url"];

							scheme, url = url[:url.find("://") + 3], url[url.find("://") + 3:];

							host = url[:url.find('/')];

							if host not in profile.Hosts:
								continue;

							path = profile.Hosts[host].find(url[url.find('/') + 1:].split("?")[0].split("/"));

							method = params["method"].lower();

							if path == None or path.resource == None or method not in path.endpoints:
								continue;
							
							elif params["method"] in path.methods:
								if url in path.methods[params["method"]]:
									for s_id in path.methods[params["method"]][url]["sources"]:
										if s_id in sources:
											del sources[s_id];
				
							path.methods[params["method"]] = {
								url : 
								{
									"request" :  {"method" : method, "headers" : "", "data" : "" , "encoded" : ""},
									"response" : { "headers" : "", "data" : "", "encoded" : "" },
									"source_id" : source_id,
									"sources" : set([source_id]),
									"path" : path,
								},
							};

							sources[source_id] = path.methods[params["method"]][url];
							print("\n%d) %s - %s %s%s"%(len(sources), event_type, params["method"], scheme, url));
							pass;

							
					req, res = sources[source_id]["request"], sources[source_id]["response"];

					if "headers" in params:

						if event_type in ["HTTP2_SESSION_SEND_HEADERS", "CORS_REQUEST", "URL_REQUEST_START_JOB", "HTTP_TRANSACTION_HTTP2_SEND_REQUEST_HEADERS"]:
							req["headers"] = params["headers"];
					
						elif event_type in ["HTTP2_SESSION_RECV_HEADERS", "HTTP_TRANSACTION_READ_RESPONSE_HEADERS"]:
							res["headers"] = params["headers"];

						else:

							print("Debug - HEADERS: Unkwown event type %s from source type %s with parameters (%s)"%(event_type, source_type, ",".join(params.keys())));

					if "bytes" in params:

						if event_type in ["URL_REQUEST_JOB_FILTERED_BYTES_READ"]:
							res["data"] += params["bytes"];

						elif event_type in ["URL_REQUEST_JOB_BYTES_READ"]:
							res["encoded"] +=  params["bytes"];
							
						else:

							print("Debug - BYTES: Unkwown event type %s from source type %s with parameters (%s)"%(event_type, source_type, ",".join(params.keys())));

					if phase == "PHASE_END" and len(res["data"]) > 0:
						handle_url_request(sources[source_id]);
						del sources[source_id];

				if buff[-1][:-3] == "}}]":
					break;

				elif nth_iteration%33 == 0:
					print("Reading : %s"%(file_stats(file, file_path)));

			print("\n\nCOMPLETED : %s\n\n"%(file_stats(file, file_path)));
			pass;

		
				
