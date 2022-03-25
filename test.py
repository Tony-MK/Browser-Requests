import classes

hosts = [ 

   classes.Host(
      name = "pinnacle.com", 
   ),
];

from scanner import scan_dir;

hosts[0].add("/0.1/sports".split("/"));
hosts[0].add("/0.1/status".split("/"))

scan_dir(dir_path = "%USERPROFILE%/Projects/BetBot/logs", hosts = hosts);