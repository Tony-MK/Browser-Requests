@echo off
set OLDPATH=%PATH%
set path=C:\MinGW\bin;%PATH%
set LIBRARY_PATH=C:\MinGW\lib;C:\Users\Tony\Desktop\MinGW\lib
set C_INCLUDE_PATH=C:\MinGW\include; C:\Users\Tony\Desktop\MinGW\include

gcc -o hello.exe hello.c

set path=%OLDPATH%