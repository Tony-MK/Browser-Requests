from typing import Any;

DEFAUT_CACHE_DURATION = 3600000;

    
class Route:

    def __init__(self, name, resource, query = dict(), top = None , cache = DEFAUT_CACHE_DURATION) -> None:
        self.top = top;
        self.name = name;
        self.cache = cache;
        self.url = self.name;
        self.resource = resource;
        self.qurey = query;
        self.routes = list();
        self.events = list();
        self.methods = dict();

        if top != None:
            self.top.routes.append(self);
            self.url = self.top.url  + "/" + self.name;
            
    
    def __str__(self):
        return "\n" + self.url + "\nRoutes : " + str(self.count()) + "\n".join([r.name for r in self.routes]) + "\n";

    def find_route(self, name) -> Any:
        for route in self.routes:
            if route.name == name:
                return route;
    
    def add(self, routes, resource, query) -> object:
        route = self.find_route(routes[0]);

        if route == None:   
            route = Route(name = routes[0], top = self, resource = resource, query = query);
            print("Caching new url : " + route.url, end = "\n");

        if len(routes) > 1:
            return route.add(routes[1:], resource, query);
        
        return (route);

    def find(self, routes) -> Any:
        route = self.find_route(routes[0]);

        if route != None  and len(routes) > 1 :
            return (route.find(routes[1:]));
        
        return (route);
        
       
    def count(self) -> int:
        return len(self.routes) + sum([r.count() for r in self.routes])

        
            
class Host(Route):
    pass;
