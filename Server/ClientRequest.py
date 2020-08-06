class ClientRequest:
    MAX_LEN_CLIENT_REQUEST = 1024 * 100
    HEADER_CONTENT_LENGTH = 'Content-Length'
    HEADER_ACTION = 'X-Action'
    ACTION_CLOSE = 'close'
    ACTION_DATA = 'data'

    def __init__(self, socket):
        self.socket = socket
        self.readConent = False

    def parse(self):
        line = ''
        count = 0
        self.isValid = False
        self.data = None
        self.contentLength = None
        self.action = None

        while line != '\r\n' and count < ClientRequest.MAX_LEN_CLIENT_REQUEST:
            line = self.readHttpLine()

            if line is None:
                break

            if line.startswith(ClientRequest.HEADER_ACTION):
                self.action = self.getHeaderVal(line)

                if not self.action is None:
                    if self.action == ClientRequest.ACTION_CLOSE or self.action == ClientRequest.ACTION_DATA:
                        self.isValid = True

            count += len(line)

        if self.readConent:
            if self.contentLength > 0 and self.contentLength < ClientRequest.MAX_LEN_CLIENT_REQUEST:
                self.data = self.readFully(self.contentLength)

        return self.isValid

    def readHttpLine(self):
        line = ''
        count = 0
        socket = self.socket

        b = socket.recv(1)

        if not b:
            return None

        while count < ClientRequest.MAX_LEN_CLIENT_REQUEST:
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

    def getHeaderVal(self, header):
        ini = header.find(':')

        if ini == -1:
            return None

        ini += 2

        fim = header.find('\r\n')

        if fim == -1:
            header = header[ini:]

        return header[ini:fim]

    def readFully(self, n):
        count = 0
        data = ''

        while count < n:
            packet = self.socket.recv(n - count)

            if not packet:
                break

            count += len(packet)
            data += packet