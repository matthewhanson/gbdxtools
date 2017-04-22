import json
from concurrent.futures import Future

VIRTUAL_IPE_URL = "https://idahoapi.geobigdata.io/v1"

from gbdxtools.ipe.error import NotFound

def resolve_if_future(future):
    if isinstance(future, Future):
        return future.result()
    else:
        return future

def get_ipe_graph(conn, graph_id):
    url = "{}/graph/{}".format(VIRTUAL_IPE_URL, graph_id)
    req = resolve_if_future(conn.get(url))
    if req.status_code == 200:
        return graph_id
    else:
        raise NotFound("No IPE graph found matching id: {}".format(graph_id))

def register_ipe_graph(conn, ipe_graph):
    url = "{}/graph".format(VIRTUAL_IPE_URL)
    res = resolve_if_future(conn.post(url, json.dumps(ipe_graph), headers={'Content-Type': 'application/json'}))
    return ipe_graph['id']

def get_ipe_metadata(conn, ipe_id, node='toa_reflectance'):
    image_response = conn.get(VIRTUAL_IPE_URL + "/metadata/idaho-virtual/{}/{}/image.json".format(ipe_id, node))
    georef_response = conn.get(VIRTUAL_IPE_URL + "/metadata/idaho-virtual/{}/{}/georeferencing.json".format(ipe_id, node))
    meta = {'image': resolve_if_future(image_response).json(), 'georef': resolve_if_future(georef_response).json()}
    return meta
