from __future__ import print_function
from gbdxtools.images.ipe_image import IpeImage
from gbdxtools.ipe.interface import Ipe
ipe = Ipe()

def reproject_params(proj):
    _params = {}
    if proj is not None:
        _params["Source SRS Code"] = "EPSG:4326"
        _params["Source pixel-to-world transform"] = None
        _params["Dest SRS Code"] = proj
        _params["Dest pixel-to-world transform"] = None
    return _params

class RadarsatImage(IpeImage):
    """
      Dask based access to landsat image backed by IPE Graphs.
    """
    def __new__(cls, path, **kwargs):
        options = {
            "product": kwargs.get("product", "radarsat")
        }

        standard_products = cls._build_standard_products(path, kwargs.get("proj", None))
        try:
            self = super(RadarsatImage, cls).__new__(cls, standard_products[options["product"]])
        except KeyError as e:
            print(e)
            print("Specified product not implemented: {}".format(options["product"]))
            raise
        self._path = path
        self._products = standard_products
        return self.aoi(**kwargs)

    @property
    def _rgb_bands(self):
        return [1]

    def get_product(self, product):
        return self.__class__(self._path, proj=self.proj, product=product)

    @staticmethod
    def _build_standard_products(path, proj):
        radarsat = ipe.RadarsatRead(path=path)
        if proj is not None:
            radarsat = ipe.Reproject(radarsat, **reproject_params(proj))
        return {
            "radarsat": radarsat
        }
