from werkzeug import Response

class JSONResponseMixin(object):
    default_mimetype = "application/json"

    @classmethod
    def from_python(cls, value, *args, **kwds):
        return cls(simplejson.dumps(value), *args, **kwds)

class JSONResponse(Response, JSONResponseMixin): pass

def get_entity_body(environ):
    if "wsgi.input" not in environ:
        # Not really something that should ever happen, but yeah.
        return ""
    parts = []
    while True:
        part = environ["wsgi.input"].read(4096)
        if not part:
            break
        parts.append(part)
    return "".join(parts)
