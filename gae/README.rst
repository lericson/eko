=====================================
 ``eko``, the HTTP request forwarder
=====================================

Introduction
============

The HTTP request forwarder does what you'd think: forwards HTTP request.

It's meant to deal with the problem of developing applications that are called
from a remote server via HTTP. Examples of this include PayPal, Facebook,
GitHub and many more.

So how does it work? Well, first off you actually need to be able to receive
HTTP requests on some server somewhere. The point is that this doesn't need to
be your local development platform.

Then in addition you run software on your local machine which connects to your
publicly available server, and relays the requests to whatever HTTP server you
prefer on the local machine.

Flowchart
=========

This is how it all looks, vaguely::

    +---------------------------------------------------------------+
    |  +----------------+                       +--------------+    |
    |  | Foreign server |                       | Local server |    |
    |  +----------------+                       +--------------+    |
    |          |                                        ^           |
    |     HTTP request                                  |           |
    |          |                                   HTTP request     |
    |          v                                        |           |
    | +------------------+   Foreign request   +-----------------+  |
    | | Remote forwarder | <-----------------> | Local forwarder |  |
    | +------------------+    Local response   +-----------------+  |
    +---------------------------------------------------------------+

Part I: Local forwarder
=======================

The local forwarder, simplified, looks like this:

 1. Make a long-standing HTTP request to remote server,
 2. forward the response's entity body to the local server,
 3. forward the local server's response to the remote forwarder.

That is to say, in a flowchart, it does this::

    [remote forwarder] <-- [local forwarder] --> [local target]

Part II: Remote forwarder
=========================

The remote forwarder consists of two subsystems; the HTTP request forwarder,
which accepts requests from remote servers; and the client handler, which
maintains an outstanding request to the local forwarder.

Request forwarding subsystem
----------------------------

 1. Wait for an HTTP request from a remote server,
 2. forward the request to the client handling subsystem,
 3. forward the response to the remote server.

Client handling subsystem
-------------------------

 1. Wait for an HTTP request from a local forwarder,
 2. wait for a request from the request forwarding subsystem,
 3. forward the request to the local forwarder,
 4. forward the response to the request forwarding subsystem.

This part could potentially do some sort of authentication mechanism.

Namespacing
===========

Of course, this all needs some sort of namespacing. The chosen method is using
the request path in HTTP requests.

So, if you'd want to use a separate namespace for PayPal, you could for example
configure PayPal's IPN to send requests to ``http://eko.example.com/paypal/``,
and similarly, the local forwarder would have to request the very same path.
