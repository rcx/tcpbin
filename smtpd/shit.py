#!/usr/bin/env python
import time,sys,os,threading

sys.path.append('..')
from common import logviewer, tcpserver
from common.settings import Settings,SSLSettings
SETTINGS = Settings('settings.py')
SSLSETTINGS = SSLSettings(SETTINGS.CERTFILE, SETTINGS.KEYFILE)

class SmtpHandler(tcpserver.ConnectionHandler):
    def handle(self):
        print self.host + ': RX begin >>>>'

        self.sock.send('220 ' + SETTINGS.FQDN + ' ESMTP Postfix\n')
        self.recvline()
        self.sock.send('250 ' + SETTINGS.FQDN + ', I am glad to meet you\n')

        while True:
            l = self.recvline()
            if l.startswith('DATA'):
                self.sock.send('354 End data with <CR><LF>.<CR><LF>\n')
                break
            self.sock.send('250 Ok\n')

        while True:
            l = self.recvline()
            if l == '.\r\n':
                break
        self.sock.send('250 Ok: queued as 12345\n')

        while True:
            l = self.recvline()
            if l.startswith('QUIT'):
                break
        print self.host + ': Successfully RX <<<<'


def main():
    if not os.path.exists(SETTINGS.LOG_DIR):
        os.makedirs(SETTINGS.LOG_DIR)
    if SETTINGS.MOTD_FILE and os.path.isfile(SETTINGS.MOTD_FILE): # motd
        import shutil
        shutil.copyfile(SETTINGS.MOTD_FILE, os.path.join(SETTINGS.LOG_DIR, SETTINGS.MOTD_FILE))

    logviewer.ViewerServer(('', SETTINGS.LOG_VIEWER_PORT), SETTINGS.AUTHKEY, SETTINGS.LOG_DIR, SSLSETTINGS if SETTINGS.LOG_VIEWER_HTTPS else None).start()
    tcpserver.DumpingServer(25, False, SmtpHandler, SETTINGS.LOG_DIR, None, SETTINGS.ANON).start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()
