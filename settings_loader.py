# see you in hell
import ssl


class Settings(object):
    def __init__(self, filename):
        with open(filename, 'r') as f:
            for l in f.readlines():
                if l:
                    exec('self.' + l)

class SSLSettings(object):
    def __init__(self, CERTFILE, KEYFILE):
        self.CERTFILE = CERTFILE
        self.KEYFILE = KEYFILE

    def wrap_socket(self, sock):
        return ssl.wrap_socket(sock, certfile=self.CERTFILE, keyfile=self.KEYFILE, server_side=True)
