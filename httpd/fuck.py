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
import BaseHTTPServer, SimpleHTTPServer
import ssl

LOG_DIR='logs'
LOG_VIEWER_PORT=8000
CERTFILE='cert.pem'
KEYFILE='privkey.pem'
MOTD_FILE='motd.txt'

def log_viewer_server():
    os.chdir(LOG_DIR)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    import SimpleHTTPServer
    import SocketServer

    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", LOG_VIEWER_PORT), Handler)
    httpd.serve_forever()

class SockWrapper(object):
    def __init__(self,x):
        self.x = x
        self.write = x.send

    def __getattr__(self,attr):
        return self.x.__getattribute__(attr)

    def read(self):
        return self.x.recv(1024)


def handle_client(is_ssl,anon,sock,addr,idx):
    print 'New connection from %s' % (addr,)
    if anon or True:
        host='anon'
    else:
        host='%s:%s'%addr
    f = open(os.path.join(LOG_DIR, '%s_%s%d_%s.txt'%(host,'ssl_' if is_ssl else '',idx,time.strftime('%s'))), 'wb')
    try:
        sock.settimeout(600)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        if is_ssl:
            wrapped_sock = ssl.wrap_socket(sock, certfile=CERTFILE, keyfile=KEYFILE, server_side=True)
        else:
            wrapped_sock = SockWrapper(sock)
        request = wrapped_sock.read()
        while request:
            print(request)
            f.write(request)
            f.flush()
            request = wrapped_sock.read()

        wrapped_sock.write("HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
        wrapped_sock.close()
    except Exception as e:
        f.write(traceback.format_exc())
    f.close()

def serve_on(port, is_ssl, anon=False):
    bindsocket = socket.socket()
    bindsocket.bind(('', port))
    bindsocket.listen(5)

    i = 0
    try:
        while True:
            newsocket, fromaddr = bindsocket.accept()
            threading.Thread(target=handle_client, args=(is_ssl,anon,newsocket,fromaddr,i)).start()
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

t1 = threading.Thread(target=serve_on, args=(443,True))
t1.daemon = True
t1.start()

t2 = threading.Thread(target=serve_on, args=(80,False))
t2.daemon = True
t2.start()

t3 = threading.Thread(target=serve_on, args=(6969,False,True))
t3.daemon = True
t3.start()

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    p.terminate()
    p.join()
    sys.exit(0)
