import os
import uuid
import threading
import mercantile
from collections import defaultdict

import numpy as np
import rasterio
from rasterio.io import MemoryFile

from gbdxtools.images.ipe_image import DaskImage
from gbdxtools import _session
from gbdxtools.images.ipe_image import _curl_pool
from gbdxtools.ipe.util import timeit

try:
    from io import BytesIO
except ImportError:
    from StringIO import cStringIO as BytesIO

import pycurl
_curl_pool = defaultdict(pycurl.Curl)

def load_url(url, bands=3):
    """ Loads a geotiff url inside a thread and returns as an ndarray """
    thread_id = threading.current_thread().ident
    _curl = _curl_pool[thread_id]
    buf = BytesIO()
    _curl.setopt(_curl.URL, url)
    _curl.setopt(_curl.WRITEDATA, buf)
    _curl.setopt(pycurl.NOSIGNAL, 1)
    _curl.perform()
    with MemoryFile(buf.getvalue()) as memfile:
      try:
          with memfile.open(driver="PNG") as dataset:
              arr = dataset.read()
      except (TypeError, rasterio.RasterioIOError) as e:
          arr = np.zeros([bands,256,256], dtype=np.float32)
          _curl.close()
          del _curl_pool[thread_id]
    return arr

class TmsImage(DaskImage):
    def __init__(self, access_token=os.environ.get("DG_MAPS_API_TOKEN"),
                 url="https://api.mapbox.com/v4/digitalglobe.nal0g75k/{z}/{x}/{y}.png",
                 zoom=22, **kwargs):
        self.zoom_level = zoom
        self._url_template = url + "?access_token={token}"
        self._tile_size = 256
        self._nbands = 3
        self._dtype = 'uint8'
        self._token = access_token
        self._cfg = self._global_dask()
        super(TmsImage, self).__init__(**self._cfg)

    def _global_dask(self):
        _tile = mercantile.tile(180, -85.05, self.zoom_level)
        nx = _tile.x * self._tile_size
        ny = _tile.y * self._tile_size
        cfg = {"shape": tuple([self._nbands] + [ny, nx]),
               "dtype": self._dtype,
               "chunks": tuple([self._nbands] + [self._tile_size, self._tile_size])}
        cfg["name"] = "image-{}".format(str(uuid.uuid4()))
        cfg["dask"] = {}
        return cfg

    def aoi(self, bounds):
        cfg = self._config_dask(bounds)
        return DaskImage(**cfg)

    def _config_dask(self, bounds):
        urls, shape = self._collect_urls(bounds)
        img = self._build_array(urls)
        cfg = {"shape": tuple([self._nbands] + list(shape)),
               "dtype": self._dtype,
               "chunks": tuple([self._nbands] + [self._tile_size, self._tile_size])}
        cfg["name"] = img["name"]
        cfg["dask"] = img["dask"]

        return cfg

    def _build_array(self, urls):
        """ Creates the deferred dask array from a grid of URLs """
        name = "image-{}".format(str(uuid.uuid4()))
        buf_dask = {(name, 0, x, y): (load_url, url) for (x, y), url in urls.items()}
        return {"name": name, "dask": buf_dask}


    def _collect_urls(self, bounds):
        params = bounds + [[self.zoom_level]]
        tile_coords = [(tile.x, tile.y) for tile in mercantile.tiles(*params)]
        xtiles, ytiles = zip(*tile_coords)
        minx = min(xtiles)
        maxx = max(xtiles)
        miny = min(ytiles)
        maxy = max(ytiles)

        urls = {(y-miny, x-minx): self._url_template.format(z=self.zoom_level, x=x, y=y, token=self._token) 
                                                for y in xrange(miny, maxy + 1) for x in xrange(minx, maxx + 1)}
        
        return urls, (self._tile_size*(maxy-miny+1), self._tile_size*(maxx-minx+1))
