from datetime import datetime
from time import perf_counter
import traceback
import base64
import asyncio
import glob
import json
import os

decode = __import__("decode")


KILO_BYTE : int = 1024
MEGA_BYTE : int = 1024 ** 2

SCREEN_WIDTH = 150

DASHED_LINE = '-'.join([''] * SCREEN_WIDTH) + "\n"

DEFAULT_CACHE_DURATION : int = 3600

BLOCK_SIZE : int = MEGA_BYTE * 32

UTC_DELTA : int = int(datetime.now().timestamp() - datetime.utcnow().timestamp()) * 1000

file_stats = lambda file, file_path : "%s (%d mins ago) %.1f/%.1f MB (%.2f%%)"%(file.name.split("\\")[-1], round(datetime.now().timestamp() - os.stat(file_path).st_mtime) / 60, file.tell() / MEGA_BYTE, os.stat(file_path).st_size / MEGA_BYTE, file.tell() / os.stat(file_path).st_size * 100 )

IGNORE_SOURCE_TYPES = [
	8 # SOCKET
]


def get_file_paths(dir_path : str, cache_duration = DEFAULT_CACHE_DURATION, latest = True, n_file_paths = 9999) -> list:

	file_paths = glob.glob(dir_path + "/*.json")

	if len(file_paths) == 0:
		return file_paths
		
	file_paths.sort(key = lambda file_path : os.stat(file_path).st_mtime , reverse = True)

	min_mtime =  datetime.now().timestamp() - cache_duration 

	if os.stat(file_paths[0]).st_mtime > min_mtime:
		return [
			file_path
			for file_path in file_paths[-n_file_paths:] if os.stat(file_path).st_mtime > min_mtime
		]

	return file_paths[:1]


def data_to_str(data: str, n_bytes = 100) -> None:
	return data if n_bytes > len(data) else data[:n_bytes] + "\n" + ".".join([""] * n_bytes) + "\n" + data[-n_bytes:]


def handle_url_request(url_req : dict) -> None:
		
	try:

		query = url_req["path"].endpoints[url_req["request"]["method"]]

		getattr(
			url_req["path"].resource, 
			query["handler"])(
				query['decoder'](
					base64.b64decode(url_req["response"]["data"]).decode('UTF-8', 'ignore')
				)
		)
	
	except json.decoder.JSONDecodeError as e:
		pass

	except Exception as e:
	
		if "/b" in url_req["path"].url and "/w" not in url_req["path"].url:
			req, resp = url_req["request"], url_req["response"]
			print(DASHED_LINE + "%s %s\nHeaders : %d Data : %d"%(req["method"].upper(), url_req["path"].url, len(req["headers"]), len(req["data"])), end = ' | ')
			print("Encoded: {:d} Headers : {:d} Data : {:d}".format(len(resp["encoded"]), len(resp["headers"]), len(resp["data"])))
			print(data_to_str(resp["data"]))
			print("FAILED TO HANDLE RESPONSE %s\n"%(e))
			traceback.print_exc()
			print(DASHED_LINE)
	


async def await_change(nth_byte: int, file, file_path: str, sleep_duration = 3, wait_duration = 900) -> None:

	timer = perf_counter()
	while os.stat(file_path).st_size == nth_byte and perf_counter() - timer < wait_duration:
		
		await asyncio.sleep(sleep_duration)

	#print("UNCHANGED - Bytes : %.3f MB %s"%(nth_byte / MEGA_BYTE, file_stats(file, file_path)))

async def valiadate_log(file_path : str):

	n_iteration = 0 

	while MEGA_BYTE > os.stat(file_path).st_size:

		if datetime.now().timestamp() - os.stat(file_path).st_mtime > 300:
			print("SMALL LOG FILE : %d Bytes %s"%(os.stat(file_path).st_size, file_path))
			return False
		
		elif not n_iteration % 10:
			print("AWAIT NEW LOG FILE : %d Bytes %s"%(os.stat(file_path).st_size, file_path))
		
		await asyncio.sleep(3)
		n_iteration += 1

def read_constants(file) -> dict:

	constants = file.readline()

	constants = json.loads(constants.strip(",\n") + "}" )["constants"]

	constants["logEventPhaseMap"] = {constants["logEventPhase"][c] : c  for c in constants["logEventPhase"]}

	constants["logSourceTypeMap"] = {constants["logSourceType"][c] : c  for c in constants["logSourceType"]}

	constants["logEventTypesMap"] = {constants["logEventTypes"][c] : c  for c in constants["logEventTypes"]}

	constants["timeTickOffset"] = int(constants["timeTickOffset"]) - UTC_DELTA

	return constants

async def read_log(hosts : list, file_path : str, cache_duration = DEFAULT_CACHE_DURATION) -> None:
	
	try:
		if await valiadate_log(file_path) == False:
			return
		
		with open(file_path, "r") as file:
			
			try:

				constants, sources = read_constants(file), dict()

			except json.decoder.JSONDecodeError:
				raise TypeError("\n\nCONSTANTS DECODE ERROR : %s\n\n"%(file_stats(file, file_path)))

			else:

				file.readline()
				file.readline()
				
				nth_byte, n_bytes, buff  = file.tell(), 0, []

				while True:

					del buff

					if datetime.now().timestamp() - os.stat(file_path).st_mtime > cache_duration:
						print("EXPIRED - Bytes : %.3f MB %s"%(nth_byte / MEGA_BYTE, file_stats(file, file_path)))

						if nth_byte > os.stat(file_path).st_size - n_bytes:

							print("\n\nCOMPLETED : %s\n\n"%(file_stats(file, file_path)))
							break

					await await_change(nth_byte, file, file_path)

					nth_byte = nth_byte - n_bytes

					file.seek(nth_byte, os.SEEK_SET)
					buff = file.read(BLOCK_SIZE)

					nth_byte += len(buff)

					buff = buff.split(",\n")
					n_bytes = len(buff[-1])

					for event in buff[:-1]:
						
						event = decode.decode_event(event, constants)

						if event == None:
							continue

						source_id, source_type = event["source"]["id"], event["source"]["type"]
						event_type = event["type"]
						timestamp = event["time"]
						params = event["params"]
						phase = event["phase"]

						del event

						if source_id not in sources:

							if "source_dependency" in params and params["source_dependency"]["id"] in sources:
								sources[source_id] = sources[params["source_dependency"]["id"]]

								# Adding to sources set
								sources[source_id]["sources"].add(source_id)

							
							elif "url" not in params or "method" not in params:
								#print("%s - Source Id %d was not Found : %s"%(event_type, source_id, params.keys()), end = "\n")
								continue

							else:

								url = params["url"]

								scheme, url = url[:url.find("://") + 3], url[url.find("://") + 3:]

								host = url[:url.find('/')]

								if host in hosts:

									path = hosts[host].find(url[url.find('/') + 1:].split("?")[0].split("/"))

									method = params["method"].lower()

									if path == None or path.resource == None or method not in path.endpoints:
										continue
									
									method_paths = path.methods.get(params["method"], {})
									for _url in list(method_paths.keys()):
										if url == _url or timestamp - method_paths[_url]["timestamp"] > DEFAULT_CACHE_DURATION:

											for s_id in method_paths[_url]["sources"]:
												if s_id in sources:
													del sources[s_id]

											del method_paths[_url]
									
									path.methods[params["method"]] = {
										url : 
										{
											"timestamp" : timestamp,
											"request" :  {"method" : method, "headers" : "", "data" : "" , "encoded" : ""},
											"response" : { "headers" : "", "data" : "", "encoded" : "" },
											"source_id" : source_id,
											"sources" : set([source_id]),
											"scheme" : scheme,
											"path" : path,
										},
									}

									sources[source_id] = path.methods[params["method"]][url]
									#print("\n%d) %s - %s %s%s"%(len(sources), event_type, params["method"], scheme, url))

						if "headers" in params:

							if event_type in ["HTTP2_SESSION_SEND_HEADERS", "CORS_REQUEST", "URL_REQUEST_START_JOB", "HTTP_TRANSACTION_HTTP2_SEND_REQUEST_HEADERS"]:
								sources[source_id]["request"]["headers"] = params["headers"]
						
							elif event_type in ["HTTP2_SESSION_RECV_HEADERS", "HTTP_TRANSACTION_READ_RESPONSE_HEADERS"]:
								sources[source_id]["response"]["headers"] = params["headers"]

							else:

								print("DEBUG - HEADERS: Unkwown event type %s from source type %s with parameters keys as (%s)"%(event_type, source_type, ",".join(params.keys())))

						if "bytes" in params:

							if event_type in ["URL_REQUEST_JOB_FILTERED_BYTES_READ"]:
								sources[source_id]["response"]["data"] += params["bytes"]

							elif event_type in ["URL_REQUEST_JOB_BYTES_READ"]:
								sources[source_id]["response"]["encoded"] +=  params["bytes"]
								
							else:

								print("DEBUG - BYTES: Unkwown event type %s from source type %s with parameters keys as (%s)"%(event_type, source_type, ",".join(params.keys())))

						if phase == "PHASE_END" and len(sources[source_id]["response"]["data"]) > 0:
							handle_url_request(sources[source_id])

	except Exception as e:
		print(("\n" * 3), e, end = "\n\n")
		
				
if __name__ == '__main__':
	pass
