import hashlib
import logging
import datetime

from werkzeug import Request, Response
from werkzeug.utils import cached_property

from eko.db import ClientInfo, StoredRequest
from eko.utils import JSONResponse

logger = logging.getLogger("eko.app")

def register_client(request):
    """Register client based on *request*, with an empty JSON list as response.
    """
    base_path = "/"  # TODO
    client_info = ClientInfo(remote_addr=request.remote_addr,
                             base_path=base_path)
    client_info.put()
    resp = JSONResponse("[]")
    resp.set_cookie("cid", str(client_info.key()))
    return resp

def client_pull(request):
    """Pull stored requests for the client specified by the *cid* cookie.

    Returns a list of dicts of format::
    
        {"headers": [[name, value], ...],
         "data": "foo"}

    Also updates ClientInfo.pulled.
    """
    client_info = ClientInfo.get(request.cookies["cid"])
    client_info.pulled = datetime.datetime.now()
    client_info.put()
    return JSONResponse(client_info.get_requests_json())

@Request.application
def client_fwd_app(request):
    """Handle client forwarding logics.

    This either registers the client, or gives the client a list of requests
    which it received. See *client_pull* for more detailed information.
    """
    if "cid" not in request.cookies:
        return register_client(request)
    else:
        return client_pull(request)

@Request.application
def request_fwd_app(request):
    """Store a request for forwading.

    Also lights a semaphore so that the interaction is snappy.
    """
    now = datetime.datetime.now()
    for client_info in ClientInfo.all():
        if request.path.startswith(client_info.base_path):
            client_info.add_request(request)
            client_info.pushed = now
            client_info.put()
    return Response("OK.\n", mimetype="text/plain")

def eko_app(environ, start_response):
    """Dispatch the request to either client forwarding or request storage.

    This is solely based on the User-Agent, which must start with 'eko/' for
    eko clients.
    """
    request = Request(environ)
    if request.user_agent.string.startswith("eko/"):
        app = client_fwd_app
    else:
        app = request_fwd_app
    return app(environ, start_response)
