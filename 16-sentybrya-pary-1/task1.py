class Data:
    def __init__(self, data, ip):
        self.data = data
        self.ip = ip
       
class Server:
    _counter = 1
    def __init__(self):
        self.ip = Server._counter
        Server._counter += 1
        self.buffer = []
        self.router = None
       
    def send_data(self, data):
        if self.router:
            self.router.buffer.append(data)
           
    def get_data(self):
        res = self.buffer.copy()
        self.buffer.clear()
        return res
       
    def get_ip(self):
        return self.ip
       
class Router:
    def __init__(self):
        self.buffer = []
        self.servers = {}
       
    def link(self, server):
        self.servers[server.get_ip()] = server
        server.router = self
       
    def unlink(self, server):
        if server.get_ip() in self.server:
            self.servers[server.get_ip()].router = None
            del self.servers[server.get_ip()]
           
    def send_data(self):
        for packet in self.buffer:
            if packet.ip in self.servers:
                self.servers[packet.ip].buffer.append(packet)
        self.buffer.clear()