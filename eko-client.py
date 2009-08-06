#!/usr/bin/env python

import time
import datetime
import logging
import urllib2
import urlparse
import optparse

try:
    import json
except ImportError:
    import simplejson as json

__version__ = "0.1"

def timedelta_to_secs(td):
    return (td.days * 86400) + td.seconds + (td.microseconds / 1000000.0)

class Headers(object):
    def __init__(self, headers):
        self.headers = headers

    def items(self):
        return self.headers

class EkoClient(object):
    logger = logging.getLogger("eko.client")
    server_url = "http://eko-eko.appspot.com/"
    min_pass_time = datetime.timedelta(seconds=5)
    user_agent = "eko/" + __version__
    running = False

    def __init__(self, target_url, namespace=None, server_url=None):
        self.target_url = target_url
        self.target_opener = urllib2.build_opener()
        self.namespace = namespace
        if server_url:
            self.server_url = server_url
        if self.namespace:
            self.server_url = urlparse.urljoin(self.server_url, namespace)
        self.server_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor)
        self.server_opener.addheaders = [("User-Agent", self.user_agent)]

    def build_target_url(self, subpath, qs=None):
        if self.namespace:
            if not subpath.startswith("/" + self.namespace):
                raise ValueError("cannot build a target url that is outside "
                                 "of namespace %r" % (self.namespace,))
            subpath = subpath[1 + len(self.namespace):]
        rv = urlparse.urljoin(self.target_url, subpath)
        if qs:
            rv += "?&"["?" in rv] + qs
        return rv

    def build_request(self, path, headers=[], data=None, qs=None):
        url = self.build_target_url(path, qs=qs)
        return urllib2.Request(url, headers=Headers(headers), data=data)

    def call_target(self, path, headers=[], data=None, qs=None):
        data = data or None  # Could be ""
        req = self.build_request(path, headers=headers, data=data, qs=None)
        self.logger.info("forward request to %s" % (req.get_full_url(),))
        # TODO Should really ignore redirects and so on here. httplib?
        try:
            resp = self.target_opener.open(req)
        except urllib2.URLError, e:
            resp = e
        self.logger.info("forward response:\n"
            "[%s] \"%s %s HTTP/1.1\" %d %s" %
            (datetime.datetime.now().strftime("%d/%b/%Y %H:%M:%S"),
             req.get_method(), req.get_selector(),
             resp.code, resp.headers.get("Content-Length", "-")))

    def call_server(self):
        try:
            return self.server_opener.open(self.server_url)
        except urllib2.URLError, e:
            if getattr(e, "code", None) != 504:
                raise

    def run_once(self):
        resp = self.call_server()
        if resp:
            for req in json.load(resp):
                self.call_target(**dict((str(k), v) for k, v in req.items()))

    def run_forever(self):
        self.running = True
        self.logger.info("eko from %s to %s" %
                         (self.server_url, self.target_url))
        while self.running:
            start = datetime.datetime.now()
            try:
                self.run_once()
            except KeyboardInterrupt:
                raise
            except:
                self.logger.exception("run_once")
            end = datetime.datetime.now()
            elapsed = end - start
            if elapsed < self.min_pass_time:
                sleep_time = self.min_pass_time - elapsed
                self.logger.debug("cooldown %s", sleep_time)
                time.sleep(timedelta_to_secs(sleep_time))
            else:
                overdue = elapsed - self.min_pass_time
                self.logger.info("server overdue: %s" % (overdue,))

class DebugEkoClient(EkoClient):
    server_url = "http://localhost:8080/"
    min_pass_time = datetime.timedelta(seconds=1)

parser = optparse.OptionParser()
parser.add_option("-v", "--verbose", dest="verbose", action="store_true")
parser.add_option("-d", "--debug", dest="debug", action="store_true")
parser.add_option("-n", "--namespace", dest="namespace", metavar="NS")
parser.add_option("-s", "--server", dest="server_url", metavar="SVR")
parser.add_option("-l", "--log", dest="log_fn", default="-")
parser.set_usage("%prog [options] <local target>")

def main():
    import sys

    opts, args = parser.parse_args()
    if not args:
        parser.print_usage(sys.stderr)
        sys.stderr.write("missing local target\n")
        sys.exit(1)
    elif len(args) > 1:
        parser.print_usage(sys.stderr)
        sys.stderr.write("can only have one local target\n")
        sys.exit(1)
    
    log_level = logging.INFO
    if opts.verbose:
        log_level = logging.DEBUG
    if opts.log_fn == "-":
        logging.basicConfig(level=log_level)
    else:
        logging.basicConfig(filename=opts.log_fn, level=log_level)

    client_tp = (EkoClient, DebugEkoClient)[bool(opts.debug)]
    client = client_tp(args[0], namespace=opts.namespace,
                       server_url=opts.server_url)
    try:
        client.run_forever()
    except KeyboardInterrupt:
        print >>sys.stderr, "Interrupted"

if __name__ == "__main__":
    main()
