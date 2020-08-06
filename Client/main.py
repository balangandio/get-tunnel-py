import sys, time, getopt, Server, Config

# CONFIG
CONFIG_LISTENING = '127.0.0.1:2424'
CONFIG_SERVER = '127.0.0.1:4242'
CONFIG_TARGET = '127.0.0.1:22'
CONFIG_PASS = ''
CONFIG_HOST = ''



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

    config = Config.Config(CONFIG_TARGET, CONFIG_SERVER if len(CONFIG_HOST) == 0 else CONFIG_HOST, CONFIG_PASS, CONFIG_SERVER)

    server = Server.Server(CONFIG_LISTENING, config)
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
