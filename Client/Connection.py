import socket, threading, ServerResponse, Logger

HEADER_ID = 'X-Id'
HEADER_PASS = 'X-Pass'
HEADER_DATA = 'X-Data'
HEADER_TARGET = 'X-Target'
HEADER_ACTION = 'X-Action'
HEADER_CONTENT = 'Content-Length'
ACTION_CREATE = 'create'
ACTION_COMPLETE = 'complete'
ACTION_DATA = 'data'


class Connection(threading.Thread):
    SERVER_CONNECT_TIMEOUT = 30
    BUFFER_SIZE = 4096

    def __init__(self, clientSoc, id, config, onCloseFunction=None):
        threading.Thread.__init__(self)
        self.serverSoc = None
        self.appSocket = clientSoc
        self.config = config
        self.logger = Logger.Logger()
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
        request += HEADER_TARGET + ': ' + self.config.target + '\r\n'
        if self.config.password is not None:
            request += HEADER_PASS + ': ' + self.config.password + '\r\n'
        request += 'Content-Type: application/octet-stream\r\n'
        request += HEADER_CONTENT + ': 0\r\n'
        request += 'Connection: Keep-Alive\r\n\r\n'

        self.log('sending connection create', Logger.LOG_INFO)
        socket.sendall(request)
        response = ServerResponse.ServerResponse(socket)
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

        response = ServerResponse.ServerResponse(socket)
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