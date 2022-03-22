from typing import Any;

DEFAUT_CACHE_DURATION = 3600;
    
   
class Route:

    def __init__(self, name, top, cache = DEFAUT_CACHE_DURATION) -> None:
        self.top = top;
        self.name = name;
        self.cache = cache;
        self.routes = list();
        self.events = list();
        self.methods = dict();

        if isinstance(top, Route):
            self.url = self.top.url + "/" + self.name;
            self.top.routes.append(self);

        else:

            self.url = self.name;

    
    def __str__(self):
        return "\n" + self.url + "\nRoutes" + "\n".join([r.name for r in self.routes]) + "\n";

    def find_route(self, name) :
        for route in self.routes:
            if route.name == name:
                return route;
    
    def add(self, routes) -> object:
        route = self.find_route(routes[0]);

        if route == None:            
            route = Route(name = routes[0], top = self);
            print("Created new route :", route.url);

        if len(routes) == 1:
            return route
        
        return route.add(routes[1:])

    def find(self, routes) -> Any:
        route = self.find_route(routes[0]);

        if isinstance(route, Route):
            return route.find(routes[1:]);

        elif isinstance(self.top, Route):
            return self;

        return None;
    
    def push(self, routes)
    


    
    def get_size(self) -> int:
        return (sum([p.get_size() for p in self.routes]) + len(self.routes)) if len(self.routes) > 0 else len(self.routes);
        
            
class Host(Route):

    def __init__(self, name, routes = []) -> None:
        super().__init__(name = name, top = None);
        list(map(self.add, routes));

