#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

struct HashTable{
	int key;
	int value;
};

typedef struct {
	char* path;
	char* map_path;
	FILE* file;
	FILE* map_file;
} Logs ;

char *MAP_FILE_PATH = "C:/Users/Tony/Desktop/Personal/Projects/BetBot/Profiles/Logs/Network/Ian Njue - Chrome 87.0.4243.0 (  Fri 11 Feb 2239  ).map";
char *FILE_PATH = "C:/Users/Tony/Desktop/Personal/Projects/BetBot/Profiles/Logs/Network/Ian Njue - Chrome 87.0.4243.0 (  Fri 11 Feb 2239  ).json";

Logs logs;

typedef struct $
{
	long start;
	long end;
}Event;

typedef struct Logs
{
	long id;
	Event* events;
} Source;

void decode_constansts()
{	
	fseek(logs.file, 0, SEEK_SET);
	char *c = (char*)malloc(sizeof(char) * 100000000);
 	fscanf(logs.file, "%[^\n]%*c", c);
 	free(c);
};

int main(int argc, char const *argv[])
{ 

	logs.path = FILE_PATH;
	logs.map_path = MAP_FILE_PATH;

	printf("Opening Log File : %s\n", logs.path );

	if ((logs.file = fopen(logs.path , "r")) == NULL) {
		printf("%s\n", "FILE NOT FOUND");
		exit(1);
	}

	printf("Creating Map File : %s\n", logs.map_path );

	if ((logs.map_file = fopen(logs.map_path , "w")) == NULL){
		printf("%s\n", "FILE NOT CREATED");
		exit(1);
	}



	decode_constansts();
	printf("\n");
	fseek(logs.file, 10, SEEK_CUR);

	long line_index, position = (0x1, ftell(logs.file));


	int code = 1;

	while(code == 1){
		/* code */
		int value = 0;

		char c = fgetc(logs.file);
		char *key = (char*)malloc(sizeof(char) * 100000000);


		switch (c)
		{

			case '\n':
				++line_index;
				Event event;
		 		event.start = position;
		 		event.end = ftell(logs.file);

		 		if (line_index%1000 == 0){
		 			printf("Code: %d Line : %d %d Bytes\r", code, line_index, event.end);
		 		};


		 	case '{':
		 		fgetc(logs.file);
			 	for (int i = 0; i < 100000000; ++i)
			 	{
			 		/* code */
			 		c = fgetc(logs.file);
			 		if (c == '"'){
			 			break;
			 		};
			 		key[i] = c;
			 	};
			 	break;
		 	
		 	case ':':
				fscanf(logs.file, "%[^,]%d", &value);
		 		printf("\nKey: %s %d",key, value);
		 		break;

		 	default:
				printf("%c", c);
		 		break;


		};
 		
 	};

 	printf("\n\nCode: %d Line : %d %d Bytes\n", code, line_index, position);
 	printf("Log Size: %d Bytes\nMap Size: %d Bytes", ftell(logs.file), ftell(logs.map_file) );
 	fclose(logs.map_file);

	fclose(logs.file); 
	return 0;
};

