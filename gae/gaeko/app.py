import logging
import datetime

from werkzeug import Request, Response
from werkzeug.exceptions import HTTPException, BadRequest

from gaeko.db import ClientInfo, StoredRequest
from gaeko.utils import JSONResponse, get_entity_body

logger = logging.getLogger("gaeko.app")

def register_client(request):
    """Register client based on *request*, with an empty JSON list as response.
    """
    base_path = request.path
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
    if client_info is None:
        raise BadRequest("bad cid")
    elif client_info.base_path != request.path:
        raise BadRequest("base_path mismatch")
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
    data = get_entity_body(request.environ)
    for client_info in ClientInfo.all():
        if request.path.startswith(client_info.base_path):
            client_info.add_request(request, data=data)
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
    try:
        return app(environ, start_response)
    except HTTPException, e:
        return e(environ, start_response)
