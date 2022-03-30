from typing import Any;

DEFAUT_CACHE_DURATION = 3600;

    
class Route:

    def __init__(self, name, resource = None, query = dict(), top = None , cache = DEFAUT_CACHE_DURATION) -> None:
        self.top = top;
        self.name = name;
        self.cache = cache;
        self.url = self.name;
        self.resource = resource;
        self.qurey = query;
        self.routes = list();
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
    
    def add(self, routes) -> object:
        route = self.find_route(routes[0]);
        
        if len(routes) == 1:
            return (Route(name = routes[0], top = self) if route == None else route)

        elif route == None:
            return (Route(name = routes[0], top = self).add(routes[1:]))

        return (route.add(routes[1:]))
        


    def find(self, routes) -> Any:
        route = self.find_route(routes[0]);

        if route != None and len(routes) > 1 :
            return (route.find(routes[1:]));
        
        return (route);
        
       
    def count(self) -> int:
        return len(self.routes) + sum([r.count() for r in self.routes])

        
            
class Host(Route):
    pass;
