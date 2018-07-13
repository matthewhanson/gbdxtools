from __future__ import print_function
from gbdxtools.images.rda_image import RDAImage
from gbdxtools.rda.interface import RDA
rda = RDA()

class MLImage(RDAImage):
    def __new__(cls, cat_id, mode="segmentation", endpoint="building-segmenter", bands="MS", **kwargs): 
        strip = rda.DigitalGlobeStrip(catId=cat_id, CRS="EPSG:4326", GSD="", 
                                      correctionType="DN", bands=bands, fallbackToTOA=True)
        dra = rda.HistogramDRA(strip)
        rgb = rda.SmartBandSelect(dra, bandSelection="RGB")
        graph = rda.StreamingML(rgb, Mode=mode, SagemakerEndpoint=endpoint)
        self = super(MLImage, cls).__new__(cls, graph)
        self.cat_id = cat_id
        return self
    
    @property
    def _rgb_bands(self):
        return [0,1,2]
    
