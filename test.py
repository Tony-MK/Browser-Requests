import classes

hosts = [ 

   classes.Host(
      name = "pinnacle.com", 
      paths =  ["/", "/0.1/sports","/0.1/leagues", "/0.1/status"]
   ),

   classes.Host(
      name = "google.com", 
      paths =  [""],
   ),
];

from scanner import scan_dir;

scan_dir(dir_path = "%USERPROFILE%/Projects/BetBot/logs", hosts = hosts);