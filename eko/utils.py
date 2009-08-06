from werkzeug import Response

class JSONResponseMixin(object):
    default_mimetype = "application/json"

    @classmethod
    def from_python(cls, value, *args, **kwds):
        return cls(simplejson.dumps(value), *args, **kwds)

class JSONResponse(Response, JSONResponseMixin): pass
