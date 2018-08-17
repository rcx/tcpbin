import ssl
import SimpleHTTPServer,BaseHTTPServer
import SocketServer
import base64
import threading,os


class AuthHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
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
                SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
            else:
                self.do_AUTHHEAD()
                self.wfile.write('Unauthorized')
        else:
            SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def translate_path(self, path):
        path = SimpleHTTPServer.SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.LOG_DIR, relpath)
        return fullpath

class ViewerServer(BaseHTTPServer.HTTPServer):
    """The main server, you pass in base_path which is the path you want to serve requests from"""
    def __init__(self, server_address, authkey='', LOG_DIR='logs', ssl_settings = None):
        self.LOG_DIR = LOG_DIR
        self.authkey = authkey
        self.ssl_settings = ssl_settings
        BaseHTTPServer.HTTPServer.__init__(self, server_address, AuthHandler)
        if self.ssl_settings:
            self.socket = self.ssl_settings.wrap_socket(self.socket)

    def serve_forever(self,):
        socket_addr = self.socket.getsockname()
        print "Serving " + ('HTTPS' if self.ssl_settings else 'HTTP') + " on", socket_addr[0], "port", socket_addr[1], "..."
        BaseHTTPServer.HTTPServer.serve_forever(self)

    def start(self):
        t = threading.Thread(target=self.serve_forever)
        t.daemon = True
        t.start()
