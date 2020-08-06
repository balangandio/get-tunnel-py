import sys, time, getopt, PasswordSet, Server

# CONFIG
CONFIG_LISTENING = '127.0.0.1:4242'
CONFIG_PASS = '123'


def print_usage():
    print '\nUsage  : python get.py -b listening -p pass'
    print 'Ex.    : python get.py -b 0.0.0.0:80 -p pass123'
    print '       : python get.py -b 0.0.0.0:80 -p passFile.pwd\n'
    print '___Password file ex.:___'
    print PasswordSet.PasswordSet.FILE_EXEMPLE

def parse_args(argv):
    global CONFIG_LISTENING
    global CONFIG_PASS

    try:
        opts, args = getopt.getopt(argv, "hb:p:", ["bind=", "pass="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ('-b', '--bind'):
            CONFIG_LISTENING = arg
        elif opt in ('-p', '--pass'):
            CONFIG_PASS = arg

def main():
    print '\n-->GetTunnelPy - Server v.' + '25/06/2017' + '\n'
    print '-->Listening: ' + CONFIG_LISTENING

    pwdSet = None

    if not CONFIG_PASS is None:
        if CONFIG_PASS.endswith('.pwd'):
            pwdSet = PasswordSet.PasswordSet()

            try:
                isValidFile = pwdSet.parseFile(CONFIG_PASS)
            except IOError as e:
                print '--#Error reading file: ' + str(type(e)) + ' - ' + str(e)
                sys.exit()

            if not isValidFile:
                print '--#Error on parsing file!\n'
                print_usage()
                return

            print '-->Pass file: ' + CONFIG_PASS + '\n'
        else:
            if (len(CONFIG_PASS) > 0):
                print '-->Pass     : yes\n'
                pwdSet = PasswordSet.PasswordSet(CONFIG_PASS)
            else:
                print '-->Pass     : no\n'

    server = Server.Server(CONFIG_LISTENING)
    server.passwdSet = pwdSet
    server.start()

    while True:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print '<-> Stopping server...'
            server.running = False
            break

if __name__ == '__main__':
    parse_args(sys.argv[1:])
    main()