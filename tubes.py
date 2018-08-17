class Tube(object):
    def __init__(self, _sock):
        self._sock = _sock
        self.buf = ''

    def readline(self):
        while True:
            i = self.buf.find('\n')
            if i >= 0:
                result, self.buf = self.buf[:i+1], self.buf[i+1:]
                return result
            else:
                self.buf += self.read()

    def __getattr__(self,attr):
        return self._sock.__getattribute__(attr)

class SocketTube(Tube):
    def __init__(self, _sock):
        super(SocketTube, self).__init__(_sock)
        self.write = _sock.send

    def read(self):
        return self._sock.recv(1024)
