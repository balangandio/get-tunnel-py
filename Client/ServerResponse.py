HEADER_ID = 'X-Id'


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
