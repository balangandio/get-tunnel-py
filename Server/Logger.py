import threading

LOG_INFO = 1
LOG_WARN = 2
LOG_ERROR = 3

logLock = threading.Lock()

class Logger:

    def printWarn(self, log):
        self.log(log)

    def printInfo(self, log):
        self.log(log)

    def printError(self, log):
        self.log(log)

    def printLog(self, log, logLevel):
        if logLevel == LOG_INFO:
            self.printInfo('<-> ' + log)
        elif logLevel == LOG_WARN:
            self.printWarn('<!> ' + log)
        elif logLevel == LOG_ERROR:
            self.printError('<#> ' + log)

    def log(self, log):
        logLock.acquire()
        print log
        logLock.release()