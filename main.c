#include <stdio.h>
#include <stdlib.h>

struct HashTable{
	int key;
	int value;
};

FILE *fileptr;
const char *FILE_NAME = "C:/Users/Tony/Desktop/Personal/Projects/browser_requests/logs/network_log.json";


void print_line(){
	char c;

	do{
  		fscanf(fileptr, "%c", &c);
  		printf("%c", c);
  	}while (c != '\n');


};

int main(int argc, char const *argv[])
{ 

	if ((fileptr = fopen(FILE_NAME, "r")) == NULL) {
		printf("%s\n", "FILE NOT FOUND");
		exit(1);
		return 0;

	};

	printf("%s %d,%d\n", "FILE FOUND", fseek(fileptr, SEEK_CUR, 2000), 2000);
 	
 	for (int i = 0; i < 2000; ++i)
 	{
 		print_line();
 	}

	printf("\nFile Length: %d\nClosing File...", ftell(fileptr));
	fclose(fileptr); 

	return 0;
};