import threading, base64, Logger, Client


class AcceptClient(threading.Thread):
    MAX_QTD_BYTES = 5000
    HEADER_BODY = 'X-Body'
    HEADER_ACTION = 'X-Action'
    HEADER_TARGET = 'X-Target'
    HEADER_PASS = 'X-Pass'
    HEADER_ID = 'X-Id'
    ACTION_CREATE = 'create'
    ACTION_COMPLETE = 'complete'
    MSG_CONNECTION_CREATED = 'Created'
    MSG_CONNECTION_COMPLETED = 'Completed'

    ID_COUNT = 0
    ID_LOCK = threading.Lock()

    def __init__(self, socket, server, passwdSet=None):
        super(AcceptClient, self).__init__()
        self.server = server
        self.passwdSet = passwdSet
        self.socket = socket

    def run(self):
        needClose = True

        try:
            head = self.readHttpRequest()

            bodyLen = self.getHeaderVal(head, AcceptClient.HEADER_BODY)
            if not bodyLen is None:
                try:
                    self.readFully(int(bodyLen))
                except ValueError:
                    pass

            action = self.getHeaderVal(head, AcceptClient.HEADER_ACTION)

            if action is None:
                self.log('client sends no action header', Logger.LOG_WARN)
                self.socket.sendall('HTTP/1.1 400 NoActionHeader!\r\nServer: GetTunnelServer\r\n\r\n')
                return

            if action == AcceptClient.ACTION_CREATE:
                target = self.getHeaderVal(head, AcceptClient.HEADER_TARGET)

                if not self.passwdSet is None:
                    passwd = self.getHeaderVal(head, AcceptClient.HEADER_PASS)

                    try:
                        passwd = base64.b64decode(passwd)
                    except:
                        passwd = None
                        pass

                    if passwd is None or not self.passwdSet.isValidKey(passwd, target):
                        self.log('client sends wrong key', Logger.LOG_WARN)
                        self.socket.sendall('HTTP/1.1 403 Forbidden\r\nServer: GetTunnelServer\r\n\r\n')
                        return

                if target is not None and self.isValidHostPort(target):
                    id = self.generateId()

                    client = Client.Client(id, self.socket, target)
                    client.onCloseFunction = self.server.removeClient
                    self.server.addClient(client)
                    self.socket.sendall('HTTP/1.1 200 '+ AcceptClient.MSG_CONNECTION_CREATED + '\r\nServer: GetTunnelServer\r\nX-Id: ' + str(id) + '\r\nContent-Type: text/plain\r\nContent-Length: 0\r\nConnection: Keep-Alive\r\n\r\n')
                    self.log('connection created - ' + str(id), Logger.LOG_INFO)
                    needClose = False
                else:
                    self.log('client sends no valid target', Logger.LOG_WARN)
                    self.socket.sendall('HTTP/1.1 400 Target!\r\nServer: GetTunnelServer\r\n\r\n')

            elif action == AcceptClient.ACTION_COMPLETE:
                id = self.getHeaderVal(head, AcceptClient.HEADER_ID)

                if not id is None:
                    client = self.server.getClient(id)

                    if not client is None:
                        client.writeSocket = self.socket

                        self.log('connection completed - ' + str(id), Logger.LOG_INFO)
                        self.socket.sendall('HTTP/1.1 200 ' + AcceptClient.MSG_CONNECTION_COMPLETED + '\r\nServer: GetTunnelServer\r\nConnection: Keep-Alive\r\n\r\n')

                        client.start()
                        needClose = False
                    else:
                        self.log('client try to complete non existing connection', Logger.LOG_WARN)
                        self.socket.sendall('HTTP/1.1 400 CreateFirst!\r\nServer: GetTunnelServer\r\n\r\n')
                else:
                    self.log('client sends no id header', Logger.LOG_WARN)
                    self.socket.sendall('HTTP/1.1 400 NoID!\r\nServer: GetTunnelServer\r\n\r\n')
            else:
                self.log('client sends invalid action', Logger.LOG_WARN)
                self.socket.sendall('HTTP/1.1 400 InvalidAction!\r\nServer: GetTunnelServer\r\n\r\n')

        except Exception as e:
            self.log('connection error - ' + str(type(e)) + ' - ' + str(e), Logger.LOG_ERROR)
        finally:
            if needClose:
                try:
                    self.socket.close()
                except:
                    pass

    def log(self, msg, logLevel):
        self.server.log(msg, logLevel)

    def readHttpRequest(self):
        request = ''
        linha = ''
        count = 0

        while linha != '\r\n' and count < AcceptClient.MAX_QTD_BYTES:
            linha = self.readHttpLine()

            if linha is None:
                break

            request += linha
            count += len(linha)

        return request

    def readHttpLine(self):
        line = ''
        count = 0
        socket = self.socket

        b = socket.recv(1)

        if not b:
            return None

        while count < AcceptClient.MAX_QTD_BYTES:
            count += 1
            line += b

            if b == '\r':
                b = socket.recv(1)
                count += 1

                if not b:
                    break

                line += b

                if b == '\n':
                    break

            b = socket.recv(1)

            if not b:
                break

        if not b:
            return None

        return line

    def getHeaderVal(self, head, header):
        if not head.startswith('\r\n'):
            header = '\r\n' + header

        if not header.endswith(': '):
            header = header + ': '

        ini = head.find(header)

        if ini == -1:
            return None

        end = head.find('\r\n', ini+2)

        ini += len(header)

        if end == -1 or ini > end or ini >= len(head):
            return None

        return head[ini:end]

    def readFully(self, n):
        count = 0

        while count < n:
            packet = self.socket.recv(n - count)

            if not packet:
                break

            count += len(packet)

    def isValidHostPort(self, hostPort):
        aux = hostPort.find(':')

        if aux == -1 or aux >= len(hostPort) -1:
            return False

        try:
            int(hostPort[aux+1:])
            return True
        except ValueError:
            return False

    def generateId(self):
        with AcceptClient.ID_LOCK:
            AcceptClient.ID_COUNT += 1
            return AcceptClient.ID_COUNT