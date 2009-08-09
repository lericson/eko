import sys
import os
from glob import glob
zip_packs = glob(os.path.join(os.path.dirname(__file__), "lib", "*.zip"))
sys.path[:] = zip_packs + sys.path
for zip_pack_fn in zip_packs:
    modname = os.path.basename(zip_pack_fn)
    modname = os.path.splitext(modname)[0]
    __import__(modname, fromlist=[""])

def main():
    from wsgiref.handlers import CGIHandler
    from gaeko.app import eko_app
    CGIHandler().run(eko_app)

if __name__ == "__main__":
    main()
