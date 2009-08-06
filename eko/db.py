import time
from google.appengine.ext import db
from google.appengine.api import memcache

import logging
import simplejson

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
            time.sleep(sleep_interval)

    def get_requests_json(self, **kwds):
        if not self.wait_requests(**kwds):
            logger.debug("found no requests for %s" % (self.key(),))
            return "[]"
        req_parts = []
        req_part = req_parts.append
        reqs = list(self.requests)
        for req in reqs:
            req_part('{"headers": %s, "data": %s}' % (req.headers, req.data))
        db.delete(reqs)
        logger.info("popped %d requests for %s" % (len(reqs), self.key()))
        return "[%s]" % (", ".join(req_parts))

    def notify_request(self):
        key = self.mc_sem_key
        if not memcache.add(key, 1, time=REQ_SEM_EXPIRE):
            if memcache.incr(key, 1) is None:
                raise ValueError("could not increment request semaphore")

    def add_request(self, request):
        hdrs = simplejson.dumps(request.headers.items())
        data = simplejson.dumps(request.data)
        req = StoredRequest(client_info=self, headers=hdrs, data=data)
        req.put()
        self.notify_request()
        logger.info("added request for %s from %s" %
                    (self.key(), request.remote_addr))

class StoredRequest(db.Model):
    client_info = db.ReferenceProperty(ClientInfo, collection_name="requests")
    created = db.DateTimeProperty(auto_now_add=True)
    headers = db.BlobProperty()
    data = db.BlobProperty()
