

class PasswordSet:
    FILE_EXEMPLE = 'master=passwd123\n127.0.0.1:22=pwd321;321pawd\n1.23.45.67:443=pass123'

    def __init__(self, masterKey=None):
        self.masterKey = masterKey

    def parseFile(self, fileName):
        isValid = False

        with open(fileName) as f:
            content = f.readlines()

        content = [x.strip() for x in content]
        content = [item for item in content if not str(item).startswith('#')]

        if len(content) > 0:
            masterKey = content[0]

            if self.splitParam(masterKey, '=') is not None and masterKey.startswith('master'):
                self.masterKey = self.splitParam(masterKey, '=')[1]

            isValid = True
            self.map = dict()

            for i, v in enumerate(content[1:]):
                hostAndPass = self.splitParam(v, '=')

                if hostAndPass is not None:
                    self.map[hostAndPass[0]] = hostAndPass[1].split(';')

        return isValid

    def isValidKey(self, key, target):
        valid = False

        if not self.masterKey == key:
            if hasattr(self, 'map'):
                if self.map.has_key(target):
                    valid = key in self.map[target]
        else:
            valid = True

        return valid


    def splitParam(self, param, c):
        index = param.find(c)

        ret = None

        if index != -1:
            ret = []
            ret.append(param[0:index])
            ret.append(param[index+1:])

        return ret