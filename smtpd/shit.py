#!/usr/bin/env python
import struct
import time
import traceback
import signal
from multiprocessing import Process
import os
import threading
import socket
import sys
import ssl

LOG_DIR='logs'
LOG_VIEWER_PORT=8001
MOTD_FILE='motd.txt'
CERTFILE='cert.pem'
KEYFILE='privkey.pem'
HTTPS=True
FQDN='hugedick.science'
AUTHKEY='mail:niggers1'

def log_viewer_server():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    import SimpleHTTPServer
    import SocketServer
    import base64

    class AuthHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_HEAD(self):
            print "HEAD: Send header"
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_AUTHHEAD(self):
            print "AUTHHEAD: Send header"
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm=\"Logs\"')
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_GET(self):
            if self.headers.getheader('Authorization') == None:
                self.do_AUTHHEAD()
                self.wfile.write('Unauthorized')
                pass
            elif self.headers.getheader('Authorization') == 'Basic '+base64.b64encode(AUTHKEY):
                SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
                pass
            else:
                self.do_AUTHHEAD()
                self.wfile.write('Unauthorized')
                pass

    # Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    # httpd = SocketServer.TCPServer(("", LOG_VIEWER_PORT), Handler)
    # httpd.serve_forever()
    httpd = SocketServer.TCPServer(("", 8001), AuthHandler)

    if HTTPS:
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile=CERTFILE, keyfile=KEYFILE, server_side=True)

    os.chdir(LOG_DIR)

    socket_addr = httpd.socket.getsockname()
    print "Serving " + ('HTTPS' if HTTPS else 'HTTP') + " on", socket_addr[0], "port", socket_addr[1], "..."
    httpd.serve_forever()

class SockWrapper(object):
    def __init__(self,_sock):
        self._sock = _sock
        self.buf = ''

    def readline(self):
        while True:
            i = self.buf.find('\n')
            if i >= 0:
                result, self.buf = self.buf[:i+1], self.buf[i+1:]
                return result
            else:
                self.buf += self._sock.recv(1024)

    def __getattr__(self,attr):
        return self._sock.__getattribute__(attr)


def handle_client(sock,addr,idx):
    from_addr, port = addr
    hostname = socket.gethostbyaddr(from_addr)[0]
    print 'New connection from %s:%s (%s)' % (hostname, port, from_addr)
    host='%s:%s'%(hostname, port)
    f = open(os.path.join(LOG_DIR, '%s_%d_%s.txt'%(host,idx,time.strftime('%s'))), 'wb')
    def recvline():
        l = wrapped_sock.readline()
        f.write(l)
        sys.stdout.write(host + ': ' + l)
        return l
    try:
        print host + ': RX begin >>>>'
        sock.settimeout(600)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        wrapped_sock = SockWrapper(sock)

        sock.send('220 ' + FQDN + ' ESMTP Postfix\n')
        recvline()
        wrapped_sock.send('250 ' + FQDN + ', I am glad to meet you\n')

        while True:
            l = recvline()
            if l.startswith('DATA'):
                wrapped_sock.send('354 End data with <CR><LF>.<CR><LF>\n')
                break
            wrapped_sock.send('250 Ok\n')

        while True:
            l = recvline()
            if l == '.\r\n':
                break
        wrapped_sock.send('250 Ok: queued as 12345\n')

        while True:
            l = recvline()
            if l.startswith('QUIT'):
                break
        wrapped_sock.close()
        print host + ': Successfully RX <<<<'

    except Exception as e:
        pass
        f.write(traceback.format_exc())
        print host + ': RX failed <<<<'
    f.flush()
    f.close()

def serve_on(port):
    bindsocket = socket.socket()
    bindsocket.bind(('', port))
    bindsocket.listen(5)
    print 'Serving on port %d ...' % (port,)

    i = 0
    try:
        while True:
            newsocket, fromaddr = bindsocket.accept()
            threading.Thread(target=handle_client, args=(newsocket,fromaddr,i)).start()
            i += 1
    except KeyboardInterrupt:
        p.terminate()
        p.join()


if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
if MOTD_FILE and os.path.isfile(MOTD_FILE): # motd
    import shutil
    shutil.copyfile(MOTD_FILE, os.path.join(LOG_DIR, MOTD_FILE))


p = Process(target=log_viewer_server)
p.start()

t1 = threading.Thread(target=serve_on, args=(25,))
t1.daemon = True
t1.start()

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    p.terminate()
    p.join()
    sys.exit(0)
