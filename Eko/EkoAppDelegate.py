"""THE APP DELEGATE :O"""

import os
import datetime
import logging

from objc import IBOutlet, IBAction, selector, object_lock
from Foundation import *
from AppKit import *

import eko

class NSLogHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        if isinstance(msg, str):
            msg = msg.decode("utf-8", "replace")
        #import pdb ; pdb.set_trace()
        NSLog(msg)

class CocoaEkoClient(NSObject, eko.EkoClient):
    @property
    def __init__(self): raise AttributeError("removed attribute")

    def initWithServer_AtURL_usingNamespace(self, server_url, target_url, namespace):
        NSLog("init: server = %r, target = %r, ns = %r" %
              (server_url, target_url, namespace))
        eko.EkoClient.__init__(self, target_url, namespace=namespace,
                               server_url=server_url)

    @classmethod
    def newAtURL_usingNamespace_(cls, target_url, namespace):
        server_url = os.environ.get("EKO_SERVER", cls.server_url)
        self = cls.new()
        self.initWithServer_AtURL_usingNamespace(server_url, target_url, namespace)
        return self

    @property
    def running(self):
        return not NSThread.currentThread().isCancelled()

    @running.setter
    def running(self, value):
        if value != self.running:
            raise ValueError("can't change running to %r" % (value,))

    def emit_request_forwarded(self, request, response):
        with object_lock(self.request_items):
            req_item = RequestItem.from_emission(request, response)
            self.request_items.append(req_item)
        NSApp.delegate().requestView.performSelectorOnMainThread_withObject_waitUntilDone_(
            "reloadData", None, True)

class RequestItemDataSource(NSObject):
#    def outlineView_child_ofItem_(self, view, child_idx, parent_item):
#        if parent_item is None:
#            return self.src[child_idx]
#        else:
#            return parent_item.data[child_idx]
#
#    def outlineView_isItemExpandable_(self, view, item):
#        return hasattr(item, "data")
#
#    def outlineView_objectValueForTableColumn_byItem_(self, view, column, item):
#        attr = column.identifier()
#        if not attr:
#            return None
#        if hasattr(item, "get_" + attr + "_view"):
#            return getattr(item, "get_" + attr + "_view")()
#        else:
#            NSLog("item repr of %s: %r" % (attr, item))
#            return getattr(item, attr, "<UNSET>")

    def numberOfRowsInTableView_(self, view):
        return len(self.src)

    def tableView_objectValueForTableColumn_row_(self, view, column, row_idx):
        attr = column.identifier()
        item = self.src[row_idx]
        if not attr:
            return
        return getattr(item, attr)

    @classmethod
    def newWithSource_(cls, src):
        self = cls.new()
        self.src = src
        return self

class RequestItem(NSObject):
    def initWithPair(self, request, response):
        self.init()
        self.request = request
        self.response = response
        self.method = request.get_method()
        self.path = request.get_selector()
        self.timestamp = datetime.datetime.now()

    @classmethod
    def from_emission(cls, request, response):
        self = cls.alloc()
        self.initWithPair(request, response)
        return self

class MyTestClass(NSObject):
    @classmethod
    def myClassMeth_(cls, arg):
        pool = NSAutoreleasePool.alloc()
        pool.init()
        NSLog("test target: %r" % (arg,))
        pool.drain()
        pool.release()

class EkoClientThread(NSThread):
    def initAtURL_usingNamespace_withItems_(self, target_url, namespace, request_items):
        self.target_url = target_url
        self.namespace = namespace
        self.request_items = request_items

    @classmethod
    def newAtURL_usingNamespace_withItems_(cls, url, ns, items):
        self = cls.new()
        self.initAtURL_usingNamespace_withItems_(url, ns, items)
        return self

    def main(self):
        pool = NSAutoreleasePool.alloc()
        pool.init()
        NSLog("A")
        NSLog("B")
        client = CocoaEkoClient.newAtURL_usingNamespace_(
            self.target_url, self.namespace)
        NSLog("C")
        client.request_items = self.request_items
        try:
            NSLog("D")
            client.run_forever()
        finally:
            NSLog("E")
            pool.drain()
            pool.release()

class EkoAppDelegate(NSObject):
    targetURL = IBOutlet()
    namespace = IBOutlet()
    requestView = IBOutlet()

    @IBAction
    def updateURLs_(self, sender):
        target_url = self.targetURL.stringValue()
        namespace = self.namespace.stringValue()
        with object_lock(self.request_items):
            self.request_items[:] = []
        self.requestView.reloadData()
        if hasattr(self, "client_thread"):
            self.client_thread.cancel()
        self.client_thread = EkoClientThread.newAtURL_usingNamespace_withItems_(
            target_url, namespace, self.request_items)
        self.client_thread.start()
        ##self.client_thread = NSThread.new()
        ##self.client_thread.initWithTarget_selector_object_(
        ##    None, selector(runEkoClientThread_, isClassMethod=True),
        ##    (target_url, namespace, self.request_items))
        ##self.client_thread.start()
        #NSThread.detachNewThreadSelector_toTarget_withObject_(
        #    selector(MyTestClass.myClassMeth_,
        #             isClassMethod=True,
        #             argumentTypes="s"),
        #    MyTestClass,
        #    "hello")
        #t = NSThread.new()
        #t.initWithTarget_selector_object_(None, selector(my_test_target), "hello")
        #t.start()
        #self.t = t

    def applicationDidFinishLaunching_(self, sender):
        logging.basicConfig(level=logging.DEBUG)
        logging.root.addHandler(NSLogHandler())
        #CFRunLoopSourceCreate(None, 0, ())
        self.request_items = NSMutableArray.new()
        self.requestView.setDataSource_(RequestItemDataSource.newWithSource_(self.request_items))
