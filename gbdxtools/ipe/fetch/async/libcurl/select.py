import os
from collections import defaultdict
import threading
from tempfile import NamedTemporaryFile
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from functools import lru_cache # python 3
except ImportError:
    from cachetools.func import lru_cache

from skimage.io import imread
import pycurl
import numpy as np

import os
import pycurl

try:
    import signal
    from signal import SIGPIPE, SIG_IGN
except ImportError:
    pass
else:
    signal.signal(SIGPIPE, SIG_IGN)

NUM_CONN = int(os.environ.get('GBDX_THREADS', 64))
print(NUM_CONN)
NUM_WORKERS = 5
MAX_RETRIES = 5

def load_urls(collection, shape=(8,256,256), max_retries=MAX_RETRIES):
    results = {}
    queue = collection
    mc = pycurl.CurlMulti()
    mc.handles = []

    num_urls = len(queue)
    num_conn = min(NUM_CONN, num_urls)

    for i in range(num_conn):
        c = pycurl.Curl()
        c.fp = None
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 5)
        c.setopt(pycurl.CONNECTTIMEOUT, 120)
        c.setopt(pycurl.TIMEOUT, 300)
        c.setopt(pycurl.NOSIGNAL, 1)
        mc.handles.append(c)

    freelist = mc.handles[:]
    num_processed = 0
    while num_processed < num_urls:
        while queue and freelist:
            url, token, index = queue.pop(0)
            c = freelist.pop()
            _, ext = os.path.splitext(urlparse(url).path)
            fp = NamedTemporaryFile(prefix='gbdxtools', suffix=ext, delete=False)
            c.fp = fp 
            c.setopt(pycurl.URL, url)
            c.setopt(pycurl.HTTPHEADER, ['Authorization: Bearer {}'.format(token)])
            c.setopt(pycurl.WRITEDATA, c.fp.file)
            mc.add_handle(c)
            # store some info
            c.index = index
            c.token = token
            c.url = url

        while 1:
            ret, num_handles = mc.perform()
            if ret != pycurl.E_CALL_MULTI_PERFORM:
                break

        # Check for curl objects which have terminated, and add them to the freelist
        while 1:
            num_q, ok_list, err_list = mc.info_read()
            for c in ok_list:
                c.fp.flush()
                c.fp.close()
                try:
                    arr = imread(c.fp.name)
                    if len(arr.shape) == 3:
                       arr = np.rollaxis(arr, 2, 0)
                    else:
                       arr = np.expand_dims(arr, axis=0)
                except Exception as e:
                    print(e)
                    arr = np.zeros(shape, dtype=np.float32)
                finally:
                    results[c.index] = arr
                    mc.remove_handle(c)
                    os.remove(c.fp.name)
                    c.fp = None
                    freelist.append(c)
                    #print("Success:", c.url, c.getinfo(pycurl.EFFECTIVE_URL))
            for c, errno, errmsg in err_list:
                _fp = cmap[h.index][-1]
                c.fp.flush()
                c.fp.close()
                os.remove(c.fp.name)
                mc.remove_handle(c)
                c.fp = None
                print("Failed: ", c.url, errno, errmsg)
                freelist.append(c)
            num_processed = num_processed + len(ok_list) + len(err_list)
            if num_q == 0:
                break
        mc.select(1.0)

    for c in mc.handles:
        if c.fp is not None:
            c.fp.close()
            c.fp = None
        c.close()

    mc.close()
    return results


