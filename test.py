MAX_CACHE_DURATION = 3600000;

class Route:

    def __init__(self, name):
        self.paths = [];
        self.name = name;
        self.cache = MAX_CACHE_DURATION;
        self.events = [];
    
    def __str__(self):
        return  '\n'.join([p.name for p in self.paths]);

class Path(Route):

    def __init__(self, name, top) -> None:
        super().__init__(name)
        self.top = top;
        pass;
    
    def find_path(self, name) :
        for path in self.paths:
            if path.name == name:
                return path;

    def push_path(self, route):
        path = Path(route[0], self);
        self.paths.append(path);
        return self.push_path(route[1:]) if len(route) > 1 else path;

    def add_path(self, route):
        path = self.find_path(route[0]);
        if path == None:
            return self.push_path(route);
        return path.add_path(route[1:]) if len(route) > 1 else path;
            
class Host(Path):

    def __init__(self, name, paths) -> None:
        super().__init__(name, top = None);

        for path in paths:
            self.add_path(path)
            pass;
    
    def __str__(self):
        return self.name + '\n' + super().__str__()
            
hosts = [ 
   Host(
       name = "guest.api.arcadia.pinnacle.com", 
       paths =  [[""], '/0.1/sports'.split("/"), '/0.1/leagues'.split("/"), '/0.1/status'.split("/")]
    ),

    Host(
       name = "google.com", 
       paths =  [[""]],
    ),
];

from scanner import scan_dir;

print(hosts[0])
scan_dir(dir_path = 'C://Users/Tony/Desktop/Projects/BetBot/logs', hosts = hosts);