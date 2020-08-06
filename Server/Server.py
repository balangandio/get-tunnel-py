import socket, threading, Logger, AcceptClient


class Server(threading.Thread):

    def __init__(self, listening, passwdSet=None):
        super(Server, self).__init__()
        self.listening = listening
        self.passwdSet = passwdSet
        self.running = False
        self.logger = Logger.Logger()
        self.isStopped = False
        self.clientsLock = threading.Lock()
        self.clients = []

    def run(self):
        try:
            self.soc = socket.socket(socket.AF_INET)
            self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.soc.settimeout(2)
            self.soc.bind((self.listening[:self.listening.find(':')], int(self.listening[self.listening.find(':') + 1:])))
            self.soc.listen(0)

            self.log('running on ' + self.listening, Logger.LOG_INFO)

            self.running = True
            while self.running:
                try:
                    c, addr = self.soc.accept()
                    c.setblocking(1)

                    self.log('opennig connection - ' + str(addr), Logger.LOG_INFO)
                    self.acceptClient(c)
                except socket.timeout:
                    continue
        except Exception as e:
            self.log('connection error - ' + str(type(e)) + ' - ' + str(e), Logger.LOG_ERROR)
        finally:
            self.running = False
            self.close()

    def acceptClient(self, socket):
        accept = AcceptClient.AcceptClient(socket, self, self.passwdSet)
        accept.start()

    def addClient(self, client):
        with self.clientsLock:
            self.clients.append(client)

    def removeClient(self, client):
        with self.clientsLock:
            self.clients.remove(client)

    def getClient(self, id):
        client = None
        with self.clientsLock:
            for c in self.clients:
                if str(c.id) == str(id):
                    client = c
                    break
        return client

    def close(self):
        if not self.isStopped:
            self.isStopped = True

            if hasattr(self, 'soc'):
                try:
                    self.soc.close()
                except:
                    pass

            with self.clientsLock:
                clientsCopy = self.clients[:]

            for c in clientsCopy:
                c.close()

            self.log('closed', Logger.LOG_INFO)

    def log(self, msg, logLevel):
        msg = 'Server: ' + msg
        self.logger.printLog(msg, logLevel)