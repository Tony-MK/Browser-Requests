DEFAUT_CACHE_DURATION = 3600000;
    
   
class Path:

    def __init__(self, name, top = None, cache = DEFAUT_CACHE_DURATION) -> None:
        self.top = top;
        self.name = name;

        self.endpoints = {};
        self.cache = cache;
        self.paths = [];
        self.events = [];
        self.url = self.get_url();
        print("Created new path :", self.url);
        pass;
    
    def get_url(self):
        if self.top == None:
            return self.name;
        return self.top.get_url() + "/" + self.name;
    
    def __str__(self):
        return  "\n".join([p.name for p in self.paths]);

    
    def find_path(self, name) :
        for path in self.paths:
            if path.name == name:
                return path;
    

    def push(self, routes):
        path = self.find_path(routes[0]);

        if path == None:            
            path = Path(routes[0], self);
            self.paths.append(path);

        return path.push(routes[1:]) if len(routes) > 1 else path;
    
    def add(self, path):
        return self.push(path.split("/"));
    
    def get_size(self, ):
        return sum([p.get_size() for p in self.paths]) + len(self.paths);
        
            
class Host(Path):

    def __init__(self, name, paths) -> None:
        super().__init__(name);
        list(map(self.add, paths));
    
    def __str__(self):
        return self.name + "\n" + super().__str__()