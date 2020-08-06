import socket, threading, Logger, ClientRequest


class Client(threading.Thread):
    ACTION_DATA = 'data'
    BUFFER_SIZE = 4096

    def __init__(self, id, readSocket, target):
        super(Client, self).__init__()
        self.targetHostPort = target
        self.id = id
        self.readSocket = readSocket
        self.logger = Logger.Logger()
        self.isStopped = False
        self.onCloseFunction = None
        self.closeLock = threading.Lock()
        self.threadEndCount = 0
        self.writeSocket = None

    def connectTarget(self):
        aux = self.targetHostPort.find(':')

        host = self.targetHostPort[:aux]
        port = int(self.targetHostPort[aux + 1:])

        self.target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.target.connect((host, port))

    def run(self):
        try:
            self.connectTarget()

            request = ClientRequest.ClientRequest(self.readSocket)
            request.readConent = False

            if not request.parse() or not Client.ACTION_DATA == request.action:
                raise Exception('client sends invalid request')

            threadRead = ThreadRelay(self.readSocket, self.target, self.finallyClose)
            threadRead.logFunction = self.log
            threadRead.start()

            threadWrite = ThreadRelay(self.target, self.writeSocket, self.finallyClose)
            threadWrite.logFunction = self.log
            threadWrite.start()
        except Exception as e:
            self.log('connection error - ' + str(type(e)) + ' - ' + str(e), Logger.LOG_ERROR)
            self.close()

    def finallyClose(self):
        with self.closeLock:
            self.threadEndCount += 1

            if self.threadEndCount == 2:
                self.close()

    def close(self):
        if not self.isStopped:
            self.isStopped = True

            if hasattr(self, 'target'):
                try:
                    self.target.close()
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
        msg = 'Client ' + str(self.id) + ': ' + msg
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
                data = self.readSocket.recv(Client.BUFFER_SIZE)
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