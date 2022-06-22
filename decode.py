import json

#IGNORE_SOURCE_TYPES = __import__('constants').IGNORE_SOURCE_TYPES
IGNORE_SOURCE_TYPES = [
    8 # SOCKET
]

def decode_event(event: dict, constants: dict) -> dict:

	try:

		event = json.loads(event);

	except json.decoder.JSONDecodeError:

		if len(event) == 0 or event[0] != "{" or event[-1] != "}":
			#print("INVALID JSON STRING (%s bytes) : %s"%(len(event), event[:100]));
			return;

		event = json.loads(event[:-1 if event[:-2] == '}]' else 3])
		pass;

	except json.decoder.JSONDecodeError as e:
		print("EVENT DECODE ERROR - " + str(e) + '\n' + event, end = "\n\n");
		return;


	if event["source"]["type"] in IGNORE_SOURCE_TYPES:
		return;

	elif "params" not in event:
		event["params"] = {};

	elif "source_dependency" in event["params"]:
		event["params"]["source_dependency"]["type"] = constants["logSourceTypeMap"][event["params"]["source_dependency"]["type"]];
		event["params"]["source_dependency"]["id"] = int(event["params"]["source_dependency"]["id"]);


	event["source"] = {
		"start_time" : constants["timeTickOffset"] + int(event["source"]["start_time"]),
		"type" : constants["logSourceTypeMap"][event["source"]["type"]],
		"id": int(event["source"]["id"])
	}
	event["time"] = constants["timeTickOffset"] + int(event["time"])
	event["phase"] = constants["logEventPhaseMap"][event["phase"]]
	event["type"]  = constants["logEventTypesMap"][event["type"]];
	return event;


def decode_headers(headers):

	if len(headers) == 1:
		headers = headers[0];
		pass;

	if headers[0].find("HTTP") != -1:
		headers[0] = "version: " + headers[0];
	
	return dict(tuple(map(lambda header : header.split(': '), headers)));


if __name__ == '__main__':
	pass
