# tcpbin

It sets up TCP sockets on ports 80(http), 443(https), 25(smtp) to listen for incoming data. Then it dumps these to a log folder which can be viewed on port 8000(https).

You can configure everything in`tcpbin.py`. See the "Additional Configuration" section below. 

## Quick start

```python
git clone https://github.com/ecx86/tcpbin.git
cd tcpbin
ln -s /etc/example.com/cert.pem cert.pem
ln -s /etc/example.com/privkey.pem privkey.pem
nano motd.txt # optional motd
service apache2 stop # or nginx
nohup python tcpbin.py > /var/log/tcpbin.log &
```

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
- **REQUEST_HANDLER**: request handler for log viewer. this defaults to SimpleHTTPServer so the script works fine standalone, but if ComplexHTTPServer is available, it uses that.

You can also select and deselect ports to serve on at the bottom of the file in `main`.

## Why?

The other http(s)bins are annoying to use when you're doing some kind of web exploitation or something low-level. Some of them, for example, reject payloads that are too large. Some even refuse connections if the wrong host header is provided. Others don't support https which is a dealbreaker if there's a same-origin policy in use. This script is also designed to be stupid simple and hassle-free to setup on any server: no Docker, no Vagrant, no Python package dependencies etc. Simply wget the script and run it.

## Closing remarks and thanks

As I hope you can see this software is a piece of crap and I wrote it so I can dump some  verification emails and to solve some CTF challenges or temporary security engagements. In other words if you use this in production please contact me so we can celebrate and get some drinks together.
