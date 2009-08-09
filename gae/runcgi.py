import sys
import os
from glob import glob
zip_packs = glob(os.path.join(os.path.dirname(__file__), "lib", "*.zip"))
sys.path[:] = zip_packs + sys.path
import werkzeug, jinja2, simplejson

def main():
    from wsgiref.handlers import CGIHandler
    from eko.app import eko_app
    CGIHandler().run(eko_app)

if __name__ == "__main__":
    main()
