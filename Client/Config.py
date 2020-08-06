import base64


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