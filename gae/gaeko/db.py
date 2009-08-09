import time
from google.appengine.ext import db
from google.appengine.api import memcache

import logging
import simplejson as json  # TODO

logger = logging.getLogger("eko.db")

REQ_SEM_EXPIRE = 3600  # an hour

class ClientInfo(db.Model):
    remote_addr = db.StringProperty()
    base_path = db.StringProperty()
    registered = db.DateTimeProperty(auto_now_add=True)
    pushed = db.DateTimeProperty()
    pulled = db.DateTimeProperty()

    @property
    def mc_sem_key(self):
        return "client_%s_sem" % (self.key(),)

    def wait_requests(self, timeout=5.0, retries=20):
        # Essentially aquires a semaphore, so could be split out.
        key = self.mc_sem_key
        sleep_interval = timeout / retries
        for attempt in xrange(retries):
            val = memcache.get(key)
            if val is not None:
                memcache.delete(key)
                return val
            try:
                time.sleep(sleep_interval)
            except KeyboardInterrupt:
                break

    def get_requests_json(self, **kwds):
        if not self.wait_requests(**kwds):
            logger.debug("found no requests for %s" % (self.key(),))
            return "[]"
        reqs = list(self.requests)
        db.delete(reqs)
        logger.info("popped %d requests for %s" % (len(reqs), self.key()))
        return "[%s]" % (", ".join(map(StoredRequest.as_json, reqs)))

    def notify_request(self):
        key = self.mc_sem_key
        if not memcache.add(key, 1, time=REQ_SEM_EXPIRE):
            if memcache.incr(key, 1) is None:
                raise ValueError("could not increment request semaphore")

    def add_request(self, request, data=None):
        sreq = StoredRequest.from_request(request, data=data)
        sreq.client_info = self
        sreq.put()
        self.notify_request()
        logger.info("request for %s from %s" % (self.key(), sreq.remote_addr))

class StoredRequest(db.Model):
    client_info = db.ReferenceProperty(ClientInfo, collection_name="requests")
    created = db.DateTimeProperty(auto_now_add=True)
    remote_addr = db.StringProperty()
    path = db.StringProperty()
    query_string = db.StringProperty()
    headers = db.BlobProperty()
    data = db.BlobProperty()

    request_properties = ("remote_addr", "path", "query_string")

    @classmethod
    def from_request(cls, request, data=None):
        hdrs = json.dumps(request.headers.items())
        data = json.dumps(data)
        kwds = dict((k, getattr(request, k)) for k in cls.request_properties)
        return cls(headers=hdrs, data=data, **kwds)

    def as_json(self):
        return ('{"path": %s, "qs": %s, "headers": %s, "data": %s}' %
                (json.dumps(self.path), json.dumps(self.query_string),
                 self.headers, self.data))
