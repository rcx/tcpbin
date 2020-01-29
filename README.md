# tcpbin

It sets up TCP sockets on ports 80(http), 443(https), 25(smtp) to listen for incoming data. Then it dumps these to a log folder which can be viewed on port 8000(https).

You can configure everything in`tcpbin.py`. See the "Additional Configuration" section below. 

## Try it online
There's a public instance available at [tcpb.in](https://tcpb.in:8000). Logs are cleared regularly to prevent abuse, but feel free to use it to quickly share files with your friends, like [transfer.sh](https://transfer.sh) or [mixtape.moe](https://mixtape.moe). Just keep in mind anyone will be able to view your files. If you'd like a private instance, you can self-host this and set a password on it (see below for instructions). At [tcpb.in:9999](http://tcpb.in:9999) there is also a [service which echoes your IP address](https://gist.github.com/ecx86/f569dd449ce7919db96523f2c18cd82f). At [tcpb.in:5000](https://tcpb.in:5000) there is a [webapp which can parse your dumped emails](https://github.com/ecx86/email-parser).

## Quick start
```
git clone https://github.com/ecx86/tcpbin.git
cd tcpbin
ln -s /etc/example.com/cert.pem cert.pem
ln -s /etc/example.com/privkey.pem privkey.pem
nano motd.txt # optional motd
service apache2 stop # or nginx
systemctl disable apache2 # or nginx
echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse # optional. avoid TIME_WAIT garbage
nohup python3 tcpbin.py > /var/log/tcpbin.log &
```

## Even quicker start
```
curl https://raw.githubusercontent.com/ecx86/tcpbin/master/tcpbin.py | python3
```

## Python 2 vs Python 3
This script has been updated to support Python 3. For the Python 2 version check out the git tag `python2`.

## Advanced configuration

You can configure the following settings in `tcpbin.py`:

- **MOTD_FILE**: filename. Will be copied to the log directory on each startup. This is because I am too lazy and incompetent to setup proper routes handlers in the log viewer http server.
- **LOG_DIR**: filename. Will be created if it doesn't exist. All the logs get dumped to here and everything in the folder will be available to access on the log viewing server.
- **LOG_VIEWER_PORT**: the port the log viewer will serve http(s) on. Don't choose a conflicting port with the actual dumping servers (i.e 80,443,25,53,etc).
- **LOG_VIEWER_HTTPS**: whether the log viewing server will serve https rather than http.
- **AUTHKEY**: optional. If not empty, make it in the format `username=password`. It specifies basic auth credentials for the log viewing server so people can't so easily steal your email confirmation links or ip address (lol)
- **CERTFILE**: filename. SSL certificate file for serving https.
- **KEYFILE**: filename. SSL private key file for serving https.
- **ANON**: boolean. If True, all logs will be anonymised (IP will be hidden)
- **FQDN**: domain name. This will be the domain name the smtp dumper will reply to `HELO`s as. This should be your domain name.
- **FILENAME_TEMPLATE**: filename format string. The logs for a connection will be saved here. Parameters are: `timestamp`, `conn_id`, `local_port`, `remote_host`, `time`.
- **TIMESTAMP_TEMPLATE**: timestamp format string. Used for strftime for log filename.
- **LOG_DIR_TEMPLATE**: python expression. gets evaluated by `eval` to choose the directory for the log. You can nest multiple directories; if the path doesn't exist it is created.
- **LOG_VIEWER_RENDERER**: request handler for log viewer. this defaults to SimpleHTTPServer so the script works fine standalone, but if ComplexHTTPServer is available, it uses that. If `None`, then the server is disabled and you can use Apache or nginx to serve it.

Lastly, if it exists, `settings.py` is executed last, meaning you can override all of the defaults in there cleanly.

You can select and deselect ports to serve on at the bottom of the file in `main`.
You can also choose to use nginx or Apache to serve the logs; in fact, this is probably preferable. Simply comment out the server line in main for port 8000.

## Why?

The other http(s)bins are annoying to use when you're doing some kind of web exploitation or something low-level. Some of them, for example, reject payloads that are too large. Some even refuse connections if the wrong host header is provided. Others don't support https which is a dealbreaker if there's a CSP in use. This script is also designed to be stupid simple and hassle-free to setup on any server: no Docker, no Vagrant, no Python package dependencies etc. Simply wget the script and run it.

## Closing remarks and thanks

As I hope you can see this software is a piece of crap and I wrote it so I can dump some  verification emails and to solve some CTF challenges or temporary security engagements. In other words if you use this in production please contact me so we can celebrate and get some drinks together.
