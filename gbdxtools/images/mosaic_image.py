import os
import time
import uuid
import threading
from string import Template
from collections import defaultdict
from itertools import chain
from functools import partial
from tempfile import NamedTemporaryFile
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from functools import lru_cache # python 3
except ImportError:
    from cachetools.func import lru_cache

from base64 import b64encode
import numpy as np
from affine import Affine
from scipy.misc import imread

import mercantile

from gbdxtools.images.tms_image import TmsMeta, TmsImage
from gbdxtools.images.meta import GeoDaskImage, DaskMeta
from gbdxtools.rda.util import AffineTransform
from gbdxtools import Interface
gbdx = Interface()

from shapely.geometry import mapping, box, shape
from shapely.geometry.base import BaseGeometry
from shapely import ops
import pyproj

import pycurl

_curl_pool = defaultdict(pycurl.Curl)

try:
    xrange
except NameError:
    xrange = range

@lru_cache(maxsize=128)
def load_url(url, shape=(8, 256, 256)):
    """ Loads a geotiff url inside a thread and returns as an ndarray """
    thread_id = threading.current_thread().ident
    _curl = _curl_pool[thread_id]
    _curl.setopt(_curl.URL, url)
    _curl.setopt(pycurl.NOSIGNAL, 1)
    _, ext = os.path.splitext(urlparse(url).path)
    with NamedTemporaryFile(prefix="gbdxtools", suffix="."+ext, delete=False) as temp: # TODO: apply correct file extension
        _curl.setopt(_curl.WRITEDATA, temp.file)
        _curl.perform()
        code = _curl.getinfo(pycurl.HTTP_CODE)
        try:
            if(code != 200):
                raise TypeError("Request for {} returned unexpected error code: {}".format(url, code))
            arr = np.rollaxis(imread(temp), 2, 0)
        except Exception as e:
            print(e)
            temp.seek(0)
            print(temp.read())
            arr = np.zeros(shape, dtype=np.uint8)
            _curl.close()
            del _curl_pool[thread_id]
        finally:
            temp.file.flush()
            temp.close()
            os.remove(temp.name)
        return arr


class EphemeralImage(Exception):
    pass


def raise_aoi_required():
    raise EphemeralImage("Image subset must be specified before it can be made concrete.")

def collect_urls(self, bounds):
    minx, miny, maxx, maxy = self._tile_coords(bounds)
    urls = {}
    for x in xrange(minx, maxx + 1):
        for y in xrange(miny, maxy + 1):
            t = mercantile.Tile(z=self.zoom_level, x=x, y=y)
            bbox = ','.join(map(str, list(mercantile.xy_bounds(t))))
            urls[(y - miny, x - minx)] = self._url.format(bbox)
    return urls, (3, self._tile_size * (maxy - miny), self._tile_size * (maxx - minx))


def preview(self):
    def fn(**kwargs):
        url = self.item['properties']['attributes']['url'].replace('{}', '{bbox-epsg-3857}')
        bbox = shape(self.item['geometry'])
        center = list(bbox.centroid.coords[0])
        layer = self.item['properties']['attributes']['layer_name']
        wmsmap(url, layer, bbox=bbox.bounds, center=center, **kwargs)
    return fn


def wmsmap(url, layer, bbox=[-180,-90,180,90], center=[0,0], zoom=10, api_key=os.environ.get('MAPBOX_API_KEY', None)):
    """
      Renders a mapbox gl map from a vector service query
    """
    try:
        from IPython.display import Javascript, HTML, display
    except:
        print("IPython is required to produce maps.")
        return

    assert api_key is not None, "No Mapbox API Key found. You can either pass in a token or set the MAPBOX_API_KEY environment variable."

    lat = center[1]
    lon = center[0]
    token = b64encode(b"flame:mosaic").decode("ascii")

    map_id = "map_{}".format(str(int(time.time())))
    display(HTML(Template('''
       <div id="map"><div id="$map_id"/></div>
       <link href='https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.2.0/leaflet.css' rel='stylesheet' />
       <style>body{margin:0;padding:0;}#map{position:relative;width:100%;height:400px;}#$map_id{position:absolute;top:0;bottom:0;width:100%;height:400px;}div.output_area .rendered_html img {margin:0}.rendered_html :link {text-decoration: none !important}</style>
    ''').substitute({"map_id": map_id})))

    js = Template("""
        require.config({
          paths: {
              ll: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.2.0/leaflet',
          }
        });

        require(['ll'], function(ll) {
            var map = L.map('$map_id', {
              center: [$lat, $lon],
              zoom: $zoom,
              maxZoom:22
            });
            
            var wmsLayer = L.tileLayer.wms('https://viewer.staging.iipfoundations.com/mapserv?', {
              layers: '$layer',
              format: 'image/png',
              map: '/usr/src/mapfiles/mapfile.map',
              transparent: true,
              maxZoom: 22,
            }).addTo(map);
        });
    """).substitute({
        "map_id": map_id,
        "url": url,
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "mbkey": api_key,
        "token": token,
        "layer": layer
    })
    display(Javascript(js))


class MosaicImage(GeoDaskImage):
    def __new__(self, _id, zoom=22, tms_meta=None, **kwargs):
        try:
            item = self.fetch(_id) 
            url = item['properties']['attributes']['url']
            self = TmsImage(zoom=zoom, 
                  collect=collect_urls, 
                  access_token=None, 
                  url=url, 
                  bounds=None, 
                  **kwargs)
            self.item = item
            self.preview = preview(self)
            return self
        except Exception as err:
            print(err)
            print('Could not find mosaic {}'.format(_id))

    @classmethod
    def fetch(self, _id):
        aoi = box(-180,-90,180,90).wkt
        query = 'item_type:DigitalGlobeOpenData AND id:{}'.format(_id)
        res = gbdx.vectors.query(aoi, query, count=1, index="vector-user-provided-gbdx-opendata")
        return res[0]
