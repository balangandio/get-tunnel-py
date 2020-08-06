import sys, time, getopt, socket, base64, threading

# CONFIG
CONFIG_LISTENING = '127.0.0.1:4242'
CONFIG_SERVER = '1.2.3.4:5678'
CONFIG_TARGET = '127.0.0.1:443'
CONFIG_PASS = ''
CONFIG_HOST = 'www.recargafacil.claro.com.br/abcdll-5xfg/'


# CONSTS
HEADER_ID = 'X-Id'
HEADER_PASS = 'X-Pass'
HEADER_DATA = 'X-Data'
HEADER_TARGET = 'X-Target'
HEADER_ACTION = 'X-Action'
HEADER_BODY = 'X-Body'
HEADER_ID = 'X-Id'
HEADER_CONTENT = 'Content-Length'
ACTION_CREATE = 'create'
ACTION_COMPLETE = 'complete'
ACTION_DATA = 'data'


class Logger:
    logLock = threading.Lock()
    LOG_INFO = 1
    LOG_WARN = 2
    LOG_ERROR = 3
    
    def printWarn(self, log):
        self.log(log)

    def printInfo(self, log):
        self.log(log)

    def printError(self, log):
        self.log(log)

    def printLog(self, log, logLevel):
        if logLevel == Logger.LOG_INFO:
            self.printInfo('<-> ' + log)
        elif logLevel == Logger.LOG_WARN:
            self.printWarn('<!> ' + log)
        elif logLevel == Logger.LOG_ERROR:
            self.printError('<#> ' + log)

    def log(self, log):
        with Logger.logLock:
            print log


class Config:

    def __init__(self, target, hostHeader, password, serverHostPort):
        self.target = target

        if len(hostHeader) == 0:
            self.hostHeader = None
        else:
            self.hostHeader = hostHeader

        if len(password) == 0:
            self.password = None
        else:
            self.password = base64.b64encode(password)

        self.serverHostPort = serverHostPort
        self.userAgent = 'GetTunnelClient'


class ServerResponse:

    def __init__(self, serverSoc):
        self.serverSoc = serverSoc
        self.isValid = False
        self.responseCode = None
        self.responseMsg = None
        self.idValue = None
        self.readEof = False

    def read(self):
        self.isValid = False

        if self.readEof:
            req = self.recvallEof(self.serverSoc)
        else:
            req = self.recvHttp(self.serverSoc)

        reqBackup = req

        if not req is None:
            index = req.find(' ')

            if index != -1:
                req = req[index + 1:]

                index = req.find(' ')
                if index != -1:
                    self.responseCode = req[:index]

                    req = req[index + 1:]
                    index = req.find('\r\n')
                    if index != -1:
                        self.responseMsg = req[:index]
                        self.isValid = True
                        self.idValue = self.getHeaderValue(reqBackup, HEADER_ID)

    def getHeaderValue(self, req, header):
        index = req.find(header)
        if index != -1:
            req = req[index:]

            index = req.find(': ')
            if index != -1:
                req = req[index + 2:]

                index = req.find('\r\n')
                if index != -1:
                    return req[:index]
        return None

    def recvHttp(self, sock):
        req = ''

        while True:
            line = self.recvHttpLine(sock)

            if line is None:
                return None

            req += line

            if req.endswith('\r\n\r\n'):
                break

        return req

    def recvHttpLine(self, sock):
        buff = ''
        while True:
            b = self.recvall(sock, 1)

            if b is None:
                return None

            buff += b

            if buff.endswith('\r\n'):
                break
        return buff

    def recvall(self, sock, n):
        data = ''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def recvallEof(self, sock):
        data = ''
        bufferLen = 1024

        while True:
            packet = sock.recv(bufferLen)
            if not packet:
                break
            data += packet

        return data


class Connection(threading.Thread):
    SERVER_CONNECT_TIMEOUT = 30
    BUFFER_SIZE = 4096

    def __init__(self, clientSoc, id, config, onCloseFunction=None):
        threading.Thread.__init__(self)
        self.serverSoc = None
        self.appSocket = clientSoc
        self.config = config
        self.logger = Logger()
        self.localId = id
        self.isRunning = False
        self.closeLock = threading.Lock()
        self.threadEndCount = 0
        self.onCloseFunction = onCloseFunction

    def run(self):
        try:
            self.isRunning = True
            self.writeSocket = self.connectToServer(Connection.SERVER_CONNECT_TIMEOUT)

            self.establishConnection()

            self.sendDataRequest(self.writeSocket)

            self.log('running', Logger.LOG_INFO)

            threadRead = ThreadRelay(self.readSocket, self.appSocket, self.finallyClose)
            threadRead.logFunction = self.log
            threadRead.start()

            threadWrite = ThreadRelay(self.appSocket, self.writeSocket, self.finallyClose)
            threadWrite.logFunction = self.log
            threadWrite.start()
        except Exception as e:
            self.log('error. ' + str(type(e)) + ' - ' + str(e), Logger.LOG_ERROR)
            self.close()

    def establishConnection(self):
        response = self.sendConnectionCreate(self.writeSocket)

        if response.isValid and response.responseCode == '200' and response.idValue is not None:
            self.connectionId = response.idValue
            self.log('connection created - ' + self.connectionId, Logger.LOG_INFO)

            self.readSocket = self.connectToServer(Connection.SERVER_CONNECT_TIMEOUT)

            response = self.sendConnectionComplete(self.readSocket)

            if response.isValid and response.responseCode == '200':
                self.log('connection completed', Logger.LOG_INFO)
            elif response.isValid:
                raise Exception('connection couldn\'t be completed - ' + response.responseMsg)
            else:
                raise Exception('server sends invalid response!')
        elif response.isValid:
            raise Exception('connection couldn\'t be created - ' + response.responseMsg)
        else:
            raise Exception('server sends invalid response!')

    def sendDataRequest(self, socket):
        request = 'POST / HTTP/1.1\r\n'
        request += 'Host: ' + self.config.hostHeader + '\r\n'
        request += 'User-Agent: ' + self.config.userAgent + '\r\n'
        request += HEADER_ACTION + ': ' + ACTION_DATA + '\r\n'
        request += 'Content-Type: application/octet-stream\r\n'
        request += HEADER_CONTENT + ': 2000000000\r\n'
        request += 'Connection: Keep-Alive\r\n\r\n'

        socket.sendall(request)

    def sendConnectionCreate(self, socket):
        request = 'POST / HTTP/1.1\r\n'
        request += 'Host: ' + self.config.hostHeader + '\r\n'
        request += 'User-Agent: ' + self.config.userAgent + '\r\n'
        request += HEADER_ACTION + ': ' + ACTION_CREATE + '\r\n'
        if self.config.password is not None:
            request += HEADER_PASS + ': ' + self.config.password + '\r\n'
        request += HEADER_TARGET + ': ' + self.config.target + '\r\n'
        request += 'Content-Type: application/octet-stream\r\n'
        request += HEADER_CONTENT + ': 0\r\n'
        request += 'Connection: Keep-Alive\r\n\r\n'

        self.log('sending connection create', Logger.LOG_INFO)
        socket.sendall(request)
        response = ServerResponse(socket)
        response.read()
        return response

    def sendConnectionComplete(self, socket):
        request = 'GET / HTTP/1.1\r\n'
        request += 'Host: ' + self.config.hostHeader + '\r\n'
        request += 'User-Agent: ' + self.config.userAgent + '\r\n'
        request += HEADER_ACTION + ': ' + ACTION_COMPLETE + '\r\n'
        request += HEADER_ID + ': ' + self.connectionId + '\r\n'
        #request += 'Content-Type: application/octet-stream\r\n'
        #request += HEADER_CONTENT + ': 0\r\n'
        #request += 'Connection: Keep-Alive\r\n\r\n'
        #request += 'Content-Length: 5\r\n'
        request += 'X-Body: 5\r\n'
        request += 'Connection: close\r\n\r\nx\r\n\r\n'

        self.log('sending connection complete', Logger.LOG_INFO)
        socket.sendall(request)

        response = ServerResponse(socket)
        response.read()
        return response

    def connectToServer(self, timeout=None):
        if not hasattr(self, 'serverAddr'):
            host = self.config.serverHostPort
            i = host.find(':')
            port = int(host[i + 1:])
            host = host[:i]
            (soc_family, soc_type, proto, _, address) = socket.getaddrinfo(host, port)[0]
            self.serverAddr = (soc_family, soc_type, proto, address)

        (soc_family, soc_type, proto, address) = self.serverAddr

        soc = socket.socket(soc_family, soc_type, proto)
        soc.setblocking(1)
        soc.settimeout(timeout)
        soc.connect(address)
        return soc

    def finallyClose(self):
        with self.closeLock:
            self.threadEndCount += 1

            if self.threadEndCount == 2:
                self.close()

    def close(self):
        if self.isRunning:
            self.isRunning = False

            if hasattr(self, 'appSocket'):
                try:
                    self.appSocket.close()
                except:
                    pass

            if hasattr(self, 'writeSocket'):
                try:
                    self.writeSocket.close()
                except:
                    pass

            if hasattr(self, 'readSocket'):
                try:
                    self.readSocket.close()
                except:
                    pass

            self.onClose()
            self.log('closed', Logger.LOG_INFO)

    def onClose(self):
        if not self.onCloseFunction is None:
            self.onCloseFunction(self)

    def log(self, msg, logLevel):
        msg = 'Conn ' + str(self.localId) + ': ' + msg
        self.logger.printLog(msg, logLevel)


class ThreadRelay(threading.Thread):
    def __init__(self, readSocket, writeSocket, closeFunction=None):
        super(ThreadRelay, self).__init__()
        self.readSocket = readSocket
        self.writeSocket = writeSocket
        self.logFunction = None
        self.closeFuntion = closeFunction

    def run(self):
        try:
            while True:
                data = self.readSocket.recv(Connection.BUFFER_SIZE)
                if not data:
                    break
                self.writeSocket.sendall(data)

            self.writeSocket.shutdown(socket.SHUT_WR)
        except Exception as e:
            if not self.logFunction is None:
                self.logFunction('threadRelay error: ' + str(type(e)) + ' - ' + str(e), Logger.LOG_ERROR)
        finally:
            if not self.closeFuntion is None:
                self.closeFuntion()


class Server(threading.Thread):
    def __init__(self, listening, config):
        threading.Thread.__init__(self)
        self.running = False
        self.listening = listening
        self.threads = []
        self.threadsLock = threading.Lock()
        self.logLock = threading.Lock()
        self.config = config
        self.logger = Logger()

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
                conn = Connection(c, addr[1], self.config, self.removeConn)
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




def print_usage():
    print '\nUsage  : python get.py -b listening -t target -s server <optinal-params>'
    print 'Optinal: --host=hostHeader\n' \
          '         --pass=passwd\n'
    print 'Ex.    : python get.py -b 127.0.0.1:1234 -t 127.0.0.1:22 -s 1.2.3.4:80 --host=host.com --pass=pass123'

def parse_args(argv):
    global CONFIG_LISTENING
    global CONFIG_TARGET
    global CONFIG_SERVER
    global CONFIG_PASS
    global CONFIG_HOST
    global CONFIG_BODY

    try:
        opts, args = getopt.getopt(argv, "hb:t:s:", ["bind=", "target=", "server=", "host=", "pass="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
		
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ("-b", "--bind"):
            CONFIG_LISTENING = arg
        elif opt in ("-t", "--target"):
            CONFIG_TARGET = arg
        elif opt in ("-s", "--server"):
            CONFIG_SERVER = arg
        elif opt in ("--host"):
            CONFIG_HOST = arg
        elif opt in ("--pass"):
            CONFIG_PASS = arg

def main():
    print '\n-->GetTunnelPy - Client v.' + '25/06/2017' + '\n'
    print '-->Server: ' + CONFIG_SERVER
    print '-->Target: ' + CONFIG_TARGET

    if len(CONFIG_HOST) > 0:
        print '-->Host  : ' + CONFIG_HOST

    if len(CONFIG_PASS) > 0:
        print '-->Pass  : yes'

    print ''

    config = Config(CONFIG_TARGET, CONFIG_SERVER if len(CONFIG_HOST) == 0 else CONFIG_HOST, CONFIG_PASS, CONFIG_SERVER)

    server = Server(CONFIG_LISTENING, config)
    server.start()

    while True:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print 'Stopping...'
            server.running = False
            break

if __name__ == '__main__':
    parse_args(sys.argv[1:])
    main()
