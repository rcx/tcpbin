import socket
import threading
import struct, os, time,sys, traceback

import tubes

class DumpingServer(object):
    def __init__(self, port, is_ssl, handler, LOG_DIR='logs', ssl_settings=None, anon=False):
        self.port = port
        self.handler = handler
        self.anon = anon
        self.ssl_settings = ssl_settings
        self.is_ssl = is_ssl
        self.LOG_DIR=LOG_DIR

    def serve_on(self):
        bindsocket = socket.socket()
        bindsocket.bind(('', self.port))
        bindsocket.listen(5)
        print 'Serving on port %d ...' % (self.port,)

        i = 0
        try:
            while True:
                newsocket, fromaddr = bindsocket.accept()
                threading.Thread(target=self.handle_client, args=(newsocket,fromaddr,i)).start()
                i += 1
        except KeyboardInterrupt:
            return

    def start(self):
        t1 = threading.Thread(target=self.serve_on)
        t1.daemon = True
        t1.start()
        return t1

    def handle_client(self, sock,addr,idx):
        from_addr, port = addr
        hostname = socket.gethostbyaddr(from_addr)[0]
        print 'New connection from %s:%s (%s)' % (hostname, port, from_addr)
        if self.anon:
            host = 'anon'
        else:
            host = '%s:%s' % (hostname, port)

        f = open(os.path.join(self.LOG_DIR, '%s_%d_%d_%s.txt' % (host,self.port, idx, time.strftime('%s'))), 'wb')
        try:
            sock.settimeout(600)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            if self.is_ssl:
                wrapped_sock = tubes.Tube(self.ssl_settings.wrap_socket(sock))
            else:
                wrapped_sock = tubes.SocketTube(sock)

            self.handler(wrapped_sock, host, f).handle()
            wrapped_sock.close()
        except Exception as e:
            f.write(traceback.format_exc())
        f.flush()
        f.close()

class ConnectionHandler(object):
    def __init__(self, sock, host, f):
        self.sock =sock
        self.host=host
        self.f=f

    def recvline(self):
        l = self.sock.readline()
        self.f.flush()
        self.f.write(l)
        sys.stdout.write(self.host + ': ' + l)
        return l
