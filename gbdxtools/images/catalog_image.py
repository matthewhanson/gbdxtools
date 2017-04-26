"""
GBDX Catalog Image Interface.

Contact: chris.helm@digitalglobe.com
"""
from __future__ import print_function
import xml.etree.cElementTree as ET
from contextlib import contextmanager
from collections import defaultdict
import os
import json
import uuid
import time

from shapely.wkt import loads
from shapely.geometry import box, shape
import requests

from gbdxtools.auth import Auth
from gbdxtools.ipe.util import calc_toa_gain_offset, ortho_params
from gbdxtools.images.ipe_image import IpeImage, DaskImage
from gbdxtools.vectors import Vectors
from gbdxtools.ipe.interface import Ipe
ipe = Ipe()

from gbdxtools import _session

band_types = {
  'MS': 'WORLDVIEW_8_BAND',
  'Panchromatic': 'PAN',
  'Pan': 'PAN',
  'pan': 'PAN'
}

class CatalogImage(IpeImage):
    """
      Catalog Image Class
      Collects metadata on all image parts and groups pan and ms bands from idaho
      Inherits from IpeImage and represents a mosiac data set of the full catalog strip
    """
    _properties = None

    def __init__(self, cat_id, band_type="MS", node="toa_reflectance", cache={}, **kwargs):
        self.interface = Auth()
        self.gbdx_connection = _session
        self.gbdx_connection.headers.update({"Authorization": "Bearer {}".format(self.interface.gbdx_connection.access_token)})
        self.vectors = Vectors()
        self._gid = cat_id
        self.cache = cache
        self._band_type = band_type
        self._pansharpen = kwargs.get('pansharpen', False)
        self._acomp = kwargs.get('acomp', False)
        if self._pansharpen:
            self._node_id = 'pansharpened'
        else:
            self._node_id = node
        self._level = kwargs.get('level', 0)
        if 'proj' in kwargs:
            self._proj = kwargs['proj']
        if '_ipe_graphs' in kwargs:
            self._ipe_graphs = kwargs['_ipe_graphs']
        else:
            self._ipe_graphs = self._init_graphs()

        super(CatalogImage, self).__init__(self._ipe_graphs, cat_id, node=self._node_id, **kwargs)


    def _query_vectors(self, query, aoi=None):
        if aoi is None:
            aoi = "POLYGON((-180.0 90.0,180.0 90.0,180.0 -90.0,-180.0 -90.0,-180.0 90.0))"
        try:
            return self.vectors.query(aoi, query=query)
        except:
            raise Exception('Unable to query for image properties, the service may be currently down.')

    @property
    def properties(self):
        if self._properties is None:
            query = 'item_type:DigitalGlobeAcquisition AND attributes.catalogID:{}'.format(self._gid)
            self._properties = self._query_vectors(query)
        return self._properties


    @property
    def metadata(self):
        meta = {}
        query = 'item_type:IDAHOImage AND attributes.catalogID:{}'.format(self._gid)
        try:
            results = self.cache[self._gid.lower()]
        except KeyError:
            print("Cache Miss: {}".format(self._gid))
            results = self._query_vectors(query)
            self.cache[self._gid.lower()] = results
        grouped = defaultdict(list)
        for idaho in results:
            vid = idaho['properties']['attributes']['vendorDatasetIdentifier']
            grouped[vid].append(idaho)

        meta['parts'] = []
        for key, parts in grouped.items():
            part = {}
            for p in parts:
                attrs = p['properties']['attributes']
                part[attrs['colorInterpretation']] = {'properties': attrs, 'geometry': shape(p['geometry'])}
            meta['parts'].append(part)

        return meta


    def aoi(self, **kwargs):
        pansharp = False
        if self._pansharpen and 'pansharpen' not in kwargs:
            pansharp = True

        bounds = self._parse_geoms(**kwargs)
        if bounds is None:
            print('AOI bounds not found. Must specify a bbox, wkt, or geojson geometry.')
            return

        cfg = self._aoi_config(bounds, **kwargs)
        return DaskImage(**cfg)


    def _init_graphs(self):
        graph = {}
        ids = []
        if self._node_id == 'pansharpened' and self._pansharpen:
            return self._pansharpen_graph()
        else:
            for part in self.metadata['parts']:
                for k, p in part.items():
                    if k == band_types[self._band_type]:
                        _id = p['properties']['idahoImageId']
                        graph[_id] = ipe.Orthorectify(ipe.IdahoRead(bucketName="idaho-images", imageId=_id, objectStore="S3"), **ortho_params(self._proj))

            return self._mosaic(graph)

    def _pansharpen_graph(self):
        pan_graphs = {}
        ms_graphs = {}

        for part in self.metadata['parts']:
            for k, p in part.items():
                vendor_id = p['properties']['vendorDatasetIdentifier']
                _id = p['properties']['idahoImageId']
                meta = self.gbdx_connection.get('http://idaho.timbr.io/{}.json'.format(_id)).result().json()
                gains_offsets = calc_toa_gain_offset(meta['properties'])
                radiance_scales, reflectance_scales, radiance_offsets = zip(*gains_offsets)
                if k == 'PAN':
                    pan_graph = ipe.Orthorectify(ipe.IdahoRead(bucketName="idaho-images", imageId=_id, objectStore="S3"), **ortho_params(self._proj))
                    pan_graph = ipe.MultiplyConst(ipe.AddConst(ipe.MultiplyConst(ipe.Format(pan_graph, dataType="4"),
                                                                                 constants=radiance_scales),
                                                               constants=radiance_offsets),
                                                  constants=reflectance_scales)
                    pan_graphs[vendor_id] = ipe.Format(ipe.MultiplyConst(pan_graph, constants=json.dumps([1000])), dataType="1")
                else:
                    ms_graph = ipe.Orthorectify(ipe.IdahoRead(bucketName="idaho-images", imageId=_id, objectStore="S3"), **ortho_params(self._proj))
                    ms_graph = ipe.MultiplyConst(ipe.AddConst(ipe.MultiplyConst(ipe.Format(ms_graph, dataType="4"),
                                                                                constants=radiance_scales),
                                                              constants=radiance_offsets),
                                                 constants=reflectance_scales)
                    ms_graphs[vendor_id] = ipe.Format(ipe.MultiplyConst(ms_graph, constants=json.dumps([1000])), dataType="1")


        pansharpened_graphs = [ipe.LocallyProjectivePanSharpen(ms_graphs[_id], pan_graphs[_id]) for _id in pan_graphs]
        return {'ms_mosaic': ipe.GeospatialMosaic(*ms_graphs.values()),
                'pan_mosiac': ipe.GeospatialMosaic(*pan_graphs.values()),
                'pansharpened': ipe.GeospatialMosaic(*pansharpened_graphs)}

    def _mosaic(self, graph, suffix=''):
        mosaic = ipe.GeospatialMosaic(*graph.values())
        idaho_id = list(graph.keys())[0]
        meta = self.gbdx_connection.get('http://idaho.timbr.io/{}.json'.format(idaho_id)).result().json()
        gains_offsets = calc_toa_gain_offset(meta['properties'])
        radiance_scales, reflectance_scales, radiance_offsets = zip(*gains_offsets)
        radiance = ipe.AddConst(ipe.MultiplyConst(ipe.Format(mosaic, dataType="4"), constants=radiance_scales), constants=radiance_offsets)
        toa = ipe.MultiplyConst(radiance, constants=reflectance_scales)
        graph.update({"mosaic{}".format(suffix): mosaic, "radiance{}".format(suffix): radiance, "toa_reflectance{}".format(suffix): toa})
        return graph
