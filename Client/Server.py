import socket, threading, Connection, Logger


class Server(threading.Thread):
    def __init__(self, listening, config):
        threading.Thread.__init__(self)
        self.running = False
        self.listening = listening
        self.threads = []
        self.threadsLock = threading.Lock()
        self.logLock = threading.Lock()
        self.config = config
        self.logger = Logger.Logger()

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
                except socket.timeout:
                    continue

                c.setblocking(1)
                self.log('opennig connection - ' + addr[0] + ':' + str(addr[1]), Logger.LOG_INFO)
                conn = Connection.Connection(c, addr[1], self.config, self.removeConn)
                conn.start()
                self.addConn(conn)
        finally:
            self.running = False
            self.close()

    def addConn(self, conn):
        with self.threadsLock:
            if self.running:
                self.threads.append(conn)

    def removeConn(self, conn):
        with self.threadsLock:
            self.threads.remove(conn)

    def close(self):
        if hasattr(self, 'soc'):
            try:
                self.soc.close()
            except:
                pass

        with self.threadsLock:
            threads = list(self.threads)

        for c in threads:
            c.close()

        self.log('closed', Logger.LOG_INFO)

    def log(self, msg, logLevel):
        msg = 'ClientServer: ' + msg
        self.logger.printLog(msg, logLevel)