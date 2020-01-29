#!/usr/bin/env python3

# ======== CONFIGURATION BLOCK ========
MOTD_FILE='motd.txt'
LOG_DIR='logs'
LOG_VIEWER_PORT=8000
LOG_VIEWER_HTTPS=False
AUTHKEY='admin:password'
CERTFILE='cert.pem'
KEYFILE='privkey.pem'
ANON=False
FQDN='example.com'
FILENAME_TEMPLATE = '{timestamp}_{conn_id}_{local_port}_{remote_host}'
LOG_DIR_TEMPLATE = "os.path.join(str(self.port), datetime.datetime.today().strftime('%Y-%m-%d'), hostname)"
TIMESTAMP_TEMPLATE = '%s'

class Disabled(object):
    pass

try:
    from ComplexHTTPServer import ComplexHTTPRequestHandler
    LOG_VIEWER_RENDERER = ComplexHTTPRequestHandler
except ImportError:
    from http.server import SimpleHTTPRequestHandler
    LOG_VIEWER_RENDERER = SimpleHTTPRequestHandler

import os
if os.name == 'nt':
    # on Windows, a different format is required.
    print('On Windows')
    TIMESTAMP_TEMPLATE = '%H:%M:%S'

if os.path.isfile('settings.py'):
    print('Loading settings from settings.py')
    exec(compile(open('settings.py').read(), 'settings.py', 'exec')) # LOL

if LOG_VIEWER_RENDERER == None:
    LOG_VIEWER_RENDERER = Disabled
# ======== END BLOCK ========


import http.server
import base64

class AuthHandler(LOG_VIEWER_RENDERER):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Logs\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        if self.server.authkey:
            if self.headers.getheader('Authorization') == None:
                self.do_AUTHHEAD()
                self.wfile.write('Unauthorized')
            elif self.headers.getheader('Authorization') == 'Basic ' + base64.b64encode(self.server.authkey):
                LOG_VIEWER_RENDERER.do_GET(self)
            else:
                self.do_AUTHHEAD()
                self.wfile.write('Unauthorized')
        else:
            LOG_VIEWER_RENDERER.do_GET(self)

    def translate_path(self, path):
        path = LOG_VIEWER_RENDERER.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.LOG_DIR, relpath)
        return fullpath

class ViewerServer(http.server.HTTPServer):
    """The main server, you pass in base_path which is the path you want to serve requests from"""
    def __init__(self, server_address, authkey='', LOG_DIR='logs', ssl_settings = None):
        self.LOG_DIR = LOG_DIR
        self.authkey = authkey
        self.ssl_settings = ssl_settings
        http.server.HTTPServer.__init__(self, server_address, AuthHandler)
        if self.ssl_settings:
            self.socket = self.ssl_settings.wrap_socket(self.socket)

    def serve_forever(self,):
        socket_addr = self.socket.getsockname()
        print("Serving " + ('HTTPS' if self.ssl_settings else 'HTTP') + " on", socket_addr[0], "port", socket_addr[1], "...")
        http.server.HTTPServer.serve_forever(self)

    def start(self):
        t = threading.Thread(target=self.serve_forever)
        t.daemon = True
        t.start()


import socket
import threading
import struct, time,sys, traceback, errno, datetime

class Tube(object):
    def __init__(self, _sock):
        self._sock = _sock
        self.buf = b''

    def readline(self):
        while True:
            i = self.buf.find(b'\n')
            if i >= 0:
                result, self.buf = self.buf[:i+1], self.buf[i+1:]
                return result
            else:
                result = self.read()
                if not result:
                    print('EOF on readline')
                    return None
                self.buf += result

    def __getattr__(self,attr):
        return self._sock.__getattribute__(attr)

class SocketTube(Tube):
    def __init__(self, _sock):
        super(SocketTube, self).__init__(_sock)
        self.write = _sock.send

    def read(self):
        return self._sock.recv(1024)


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
        print('Serving on port %d ...' % (self.port,))

        i = 0
        try:
            while True:
                newsocket, fromaddr = bindsocket.accept()
                newsocket.settimeout(300.0)
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
        try:
            hostname = socket.gethostbyaddr(from_addr)[0]
        except:
            hostname = from_addr
        print('New connection from %s:%s (%s)' % (hostname, port, from_addr))
        if self.anon:
            hostname = 'anon'
        host = '%s:%s' % (hostname, port)

        log_filename = FILENAME_TEMPLATE.format(timestamp=time.strftime(TIMESTAMP_TEMPLATE), conn_id=idx, local_port=self.port, remote_host=host) + self.handler.get_file_ext()
        if os.name == 'nt':
            log_filename = log_filename.replace(':', ';') # no colons are allowed on windows
        log_file_dir = os.path.join(self.LOG_DIR, eval(LOG_DIR_TEMPLATE)) # lol eval
        try:
            os.makedirs(log_file_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                sys.stderr.write('Failed to create log directory %s\n' % (log_file_dir,))
                log_file_dir = self.LOG_DIR
        log_full_filename = os.path.join(log_file_dir, log_filename)
        f = open(log_full_filename, 'wb')
        try:
            sock.settimeout(600)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            if self.is_ssl:
                wrapped_sock = Tube(self.ssl_settings.wrap_socket(sock))
            else:
                wrapped_sock = SocketTube(sock)

            self.handler(wrapped_sock, host, f).handle(logfile=log_full_filename)
            wrapped_sock.shutdown(socket.SHUT_WR)
            wrapped_sock.close()
        except Exception as e:
            f.write(traceback.format_exc().encode('utf-8'))
        f.flush()
        f.close()

class ConnectionHandler(object):
    def __init__(self, sock, host, f):
        self.sock =sock
        self.host=host
        self.f=f

    def recvline(self):
        l = self.sock.readline()
        if not l:
            return l
        self.f.flush()
        self.f.write(l)
        sys.stdout.write(self.host + ': ' + l.decode('utf-8'))
        return l

    @staticmethod
    def get_file_ext():
        return '.txt'


import ssl


class SSLSettings(object):
    def __init__(self, CERTFILE, KEYFILE):
        self.CERTFILE = CERTFILE
        self.KEYFILE = KEYFILE

    def wrap_socket(self, sock):
        return ssl.wrap_socket(sock, certfile=self.CERTFILE, keyfile=self.KEYFILE, server_side=True)


SSLSETTINGS = SSLSettings(CERTFILE, KEYFILE)

class HttpHandler(ConnectionHandler):
    def handle(self, **kwargs):
        request = self.sock.read()
        while request:
            print(request)
            self.f.write(request)
            self.f.flush()
            request = self.sock.read()
        self.sock.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")

class AnonFileHandler(ConnectionHandler):
    def handle(self, logfile=''):
        request = self.sock.read()
        while request:
            self.f.write(request)
            self.f.flush()
            request = self.sock.read()
        file_url = ('https' if LOG_VIEWER_HTTPS else 'http') + '://' + FQDN + ':' + str(LOG_VIEWER_PORT) + os.sep + logfile[len(LOG_DIR)+1:]
        print('Finished receiving file %s' % (logfile,))
        print('Available at %s' % (file_url,))
        self.sock.write((file_url+'\n').encode('utf-8'))

    @staticmethod
    def get_file_ext():
        return ''


class SmtpHandler(ConnectionHandler):
    def handle(self, **kwargs):
        print(self.host + ': RX begin >>>>')

        self.sock.send((b'220 ' + FQDN.encode('ascii') + b' ESMTP Postfix\r\n'))
        self.recvline()
        self.sock.send(b'250 ' + FQDN.encode('ascii') + b', I am glad to meet you\r\n')

        while True:
            l = self.recvline()
            if l == None:
                print(self.host + ': Socket closed <<<<')
                return
            if l.startswith(b'DATA'):
                self.sock.send(b'354 End data with <CR><LF>.<CR><LF>\r\n')
                break
            if l.startswith(b'QUIT'):
                print(self.host + ': Successfully RX <<<<')
                return
            self.sock.send(b'250 Ok\r\n')

        while True:
            l = self.recvline()
            if l == None:
                print(self.host + ': Socket closed <<<<')
                return
            if l == b'.\r\n':
                break
        self.sock.send(b'250 Ok: queued as 12345\r\n')

        while True:
            l = self.recvline()
            if l == None:
                print(self.host + ': Socket closed <<<<')
                return
            if l.startswith(b'QUIT'):
                break
        print(self.host + ': Successfully RX <<<<')

def main():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    if MOTD_FILE and os.path.isfile(MOTD_FILE): # motd
        import shutil
        shutil.copyfile(MOTD_FILE, os.path.join(LOG_DIR, MOTD_FILE))

    if LOG_VIEWER_RENDERER != Disabled:
        print('Using %s as the log viewer renderer' % (LOG_VIEWER_RENDERER.__name__))
        ViewerServer(('', LOG_VIEWER_PORT), AUTHKEY, LOG_DIR, SSLSETTINGS if LOG_VIEWER_HTTPS else None).start()
    else:
        print('Log viewing server disabled')

    DumpingServer(80, False, HttpHandler, LOG_DIR, None, ANON).start()
    DumpingServer(443, True, HttpHandler, LOG_DIR, SSLSETTINGS, ANON).start()
    DumpingServer(6969, False, AnonFileHandler, LOG_DIR, None, True).start()
    DumpingServer(6970, True, AnonFileHandler, LOG_DIR, SSLSETTINGS, True).start()
    DumpingServer(25, False, SmtpHandler, LOG_DIR, None, ANON).start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()


