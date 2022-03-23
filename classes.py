from typing import Any;

DEFAUT_CACHE_DURATION = 3600;
    
   
class Route:

    def __init__(self, name, top = None, cache = DEFAUT_CACHE_DURATION) -> None:
        self.top = top;
        self.name = name;
        self.cache = cache;
        self.routes = list();
        self.events = list();
        self.methods = dict();

        if isinstance(top, Route):
            self.url = self.top.url  + "/" + self.name;
            self.top.routes.append(self);

        else:

            self.url = self.name;
            pass;

    
    def __str__(self):
        return "\n" + self.url + "\nRoutes : " + str(self.get_size()) + "\n".join([r.name for r in self.routes]) + "\n";

    def find_route(self, name) :
        for route in self.routes:
            if route.name == name:
                return route;
    
    def add(self, routes) -> object:
        route = self.find_route(routes[0]);

        if route == None:   
            route = Route(name = routes[0], top = self);
            print("Caching new url : " + route.url, end = '\r')

        
        return (route if len(routes) < 2 else route.add(routes[1:]))

    def find(self, routes) -> Any:
        route = self.find_route(routes[0]);

        if len(routes) > 1:
            if route != None:
                return (route.find(routes[1:]));
        
        return (route);
    
    def get_size(self) -> int:
        return (sum([r.get_size() for r in self.routes]) + len(self.routes));
        
            
class Host(Route):
    pass;
