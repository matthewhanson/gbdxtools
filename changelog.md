0.16.4
* Adding support for Sentinel1 and MODIS Imagery
* Re-adding the feature info click handler in vector maps 

0.16.3 
* several small bug fixes. 
* pinned numpy to < 1.16.0 for pip installs to work
* deprecated image.display_stats
* fixed wv4 ndvi_bands
* fixes for s3 upload logic and documentation 
* rda types of byte are now uint8 so the reported dtype matches data dtype when fetched

0.16.2
* New vector styles and style expressions for mapping vectors via `gbdx.vectors.map()`
* RDA based images can now be materialized to s3 via `image.materialize()`
* added a materialize_status method for checking jobs
* refactored the vector map methods to make use of a shared mapping template
 

0.16.1
* Added method for checking if a catalog ID has been ordered (`CatalogImage.is_ordered(catid)`)
* Added method for checking if a catalog ID can be acomp'd (`CatalogImage.acomp_available(catid)`)

0.16.0
* Depricated the base_layer_match method, now user .rgb(histogram="match")
* Updated docs for image classes 
* changed window_at to accept window_shape for parity with other windowing methods
* When images fail to successfully fetch an image tile from RDA, an error is now thrown 


0.15.13 
* Added TemplateImage for rendering template id with params from RDA
* using RDA's DRA operator for image.preview()
* removes overlap warning when an AOI is partially beyond image extent, replaced with warning for fully disjoin AOIs
* use RadionmetricDRA instead of HistogramDRA 

0.15.12 
* Added window_cover method
* Fixes for TmsImage bounds
* Adding spec='rgb' to geotiff creation
* Cleaned up image class examples with latest code

0.15.11 
* Added the ability to pansharpen landsat and ikonos imagery

0.15.10 
* fixed bug with geotiff method on imagery requiring spec
* cleaned up deprecation code to ignore deprecations from other dependencies 

0.15.9
* changing `spec` to `band_type` for landsat imagery
* fix for calling geotransform.rev from inside warp with a numpy array 
 
0.15.8 
* plot fixes for histogram='ignore'
* ipe deprecation fixes  

0.15.7
* Deprecated the use of ipe and IPE and replaced with rda/RDA
* wrapped the dask method rechunk to return an instance of GeoDaskArray
* fixed bug with single value indexing of imagery
* Added support for radarsat imagery.
* fixed a bug in how we return results from `__geotransform__.rev` - now returns tuples instead of ndarrays
* added method `window_at` to return windows centered on a location of a given pixel x/y size
* searching catalogIDs with keywords in CatalogImages


0.15.6 
* Fixed a band selection issue in image previews
* changed the way we talked to the Openlayers objects in preview
* Added a BrowseImage class for fetching and indexing browse imagery by catalogIDs
* rgb and plot methods support base layer matching via browse imagery via the `blm_source="browse"` flag 

0.15.5 
* fix for missing import in geo mixin

0.15.4 
* Fixed preview map scales and offset for better colors
* Refactored geo/plot mixin to support better band index calcs
* fixed passing bands to plot method for 3 band and 1 band plots

0.15.3
* Wrapping map_blocks to return geodaskimages instead of a dask array
* Fixing the calls to tiles inside the preview method so preview will work again
* Fixes the return xmin/ymin in slice_padded, was lost in the refactor. Edge case padding of image collars.
* added support for controlling the clipping of pixel bounds to the image extent

0.15.2
* Casting task env ports to lists so they can be serialized in gbdx notebooks.

0.15.1
* Fixed IdahoImage spec="1b" and protecting RDAGeoAdapter from missing georef metadata (for 1b access)
* WV04 Image support
* Sentinel data supprt via CatalogImage, but must pass a recordID. 

0.15.0
* Refactored the image class core dask pattern
* No longer building complex graphs for Worldview, using DigitalGlobeStrip RDA operator
* Dropped support for passing in "product" to various image classes

0.14.7
* fixes geotransform shift when padding indexes images
* fixes affine geotransform rev off-by-one rounding error

0.14.3
* Removing calls to idaho.timbr.io for metadata
* Using the ipe.TOAReflectance Op
* Support for Acomp on WV2, WV3, QB02, and GE01 image classes

0.14.0
* pin dask to 0.16.0 and fix subclasshook in images/meta
* respect image bucket names correctly
* removing requirement for rasterio
* trimming dask graphs when spatially indexing images

0.13.9
* support for sentinel2 images
* better error reporting for missing metadata and missing/corrupt catalog data
* bug fixes
* pinning to dask 0.15.4

0.13.8
* pinning dask to 0.15.2
* misc bug fixes 

0.13.7
* using dask.store for mutlithreaded geotiff creation

0.13.4
______
* retry functionality for Ipe Image classes
* dask delayed client side reprojection and orthorectification via warp
* global dask threadpool for `.read` operations
* gsd support for mosaic op based images
* handling of errors in workflow status calls
* misc bugfixes

0.13.1
------
* fix to enable proper installation via pypi

0.13.0
-------
* upgrading to new dask version support (dask >= 0.15.1)
* using the __new__ pattern for image classes
* fixes for creating geotiffs from images  

0.11.14
-------
* orthorectify parameters bugfix

0.11.13
-------
* dtype fix for the to_geotiff method

0.11.12
-------
* Handle ipe image metadata errors

0.11.11
-------
* more verbose error when idaho cannot download chip

0.11.10
-------
* Minor patch to use new serverside IPE ids

0.11.9
------
* Fix signals exception handling for Windows OS.

0.11.8
------
* add LandsatImage class

0.11.7
------
* pin version of dask====0.13.0

0.11.6
------
* Add optional index parameter to vector aggregations

0.11.5
------
* Add in vector aggregation support (see examples/vectors_aggregation.py)

0.11.4
------
* Default vector service classes to use catalog indexes instead of the searching through all documents

0.11.3
------
* Adds CatalogImage and IdahoImage classes 

0.11.2
------
* upgrade gbdx-auth==0.2.4.  Allows env vars for gbdx authentication

0.11.1
------
* fix #99 and #100

0.11.0
------
* upgrade to catalog/v2 usage

0.10.2
------
* fix for breaking change in VectorService

0.10.1
-----
* Added new task_registry.update() function to update tasks in place

0.10.0
-----
* refactored the way auth is handled in gbdxtools.interface into a singleton pattern to support direct importing of module classes. Classes can now auth themselves. 

0.9.6
-----
* update gbdx.vectors.query() to be able to return more than 1000 results (uses paging service on the backend)
* new function gbdx.vectors.query_iteratively() that returns a generator instead of a list.  Useful if a lot of results.

0.9.5
-----
* update gbdx-auth to 0.2.2: allows new env var GBDX_ACCESS_TOKEN

0.9.4
-----
* add "host" parameter to interface kwargs for dev purposes

0.9.3
-----
* add workflow callback support:  wf = workflow([task], callback='callback_url')

0.9.2
-----
* shorten task name UUIDs to 8 characters for readability

0.9.1
-----
* add gbdx.ordering.heartbeat() function

0.9.0
-----
* add workflow.stdout, workflow.stderr, workflow.task_ids
* add gbdx.workflow.get_stdout(), gbdx.workflow.get_stderr(), gbdx.workflow.get()

0.8.1
-----
* upgrade requests version

0.8.0
-----
* Added get_tms_layers function to idaho module

0.7.2
-----
* Fix a bug in batchworkflow expansion

0.7.1
-----
* Update batchworkflows in simpleworkflow to use new jinja templating

0.7.0
-----
* Get image chip from catalog id and rectangle
* Removed shapely from dependencies

0.6.8
-----
* Updated leaflet javascript links in leafletmap_template which is used to create idaho slippy maps

0.6.7
-----
* Add gbdx.vectors.query, gbdx.vectors.create, and gbdx.vectors.create_from_wkt

0.6.6
-----
* simpleworkflows.savedata now uses persist flag
* s3.download maintains directory structure

0.6.5
-----
* Can now set impersonation_allowed flag

0.6.4
-----
* Fixed batch workflow bugs

0.6.3
-----
* Handle case where output port description is absent

0.6.2
-----
* Added support for image location API orders.location()

0.6.1
-----
* handle case of spurious keys in s3.download()

0.6.0
-----
* add TaskRegistry class to Interface

0.5.5
-----
* add format & bands parameters to get_idaho_chip_url() function

0.5.4
-----
* add get_idaho_chip_url function

0.5.3
-----
* bugfix in idaho.describe_idaho_images function (was showing wrong sensorPlatformName)

0.5.2
-----
* Add gbdx.catalog.get() and gbdx.catalog.get_strip_metadata()
* Fix bug in simpleworkflow status

0.5.1
-----
* Fix bumpversioning bug.

0.5.0
-----
* Python 3 support (3.3, 3.4, 3.5)

0.4.0
-----
* Batch workflow creation supported.  When you send in an array of values to a workflow input, a batch workflow is automatically created.

0.3.4
-----
* Fix bug with multiplex port assignment.

0.3.3
-----
* Fix bug with output multiplex ports.  Now the root multiplex port is not added to the workflow launched unless another input from another task explicitly refers to it.

0.3.2
-----
* quick change to catalog.get_most_recent_images(): now it takes a list of catalog results as an argument.

0.3.1
-----
* Added multiplex output support to simpleworkflow tasks.

0.3.0
-----
* catalog.search_address() and catalog.search_point() now take the same search filtering parameters as catalog.search().  As a breaking-change side effect, catalog.search_address() and catalog.search_point() now return a list of results, rather than a result-set dictionary.  Also, rather than a singular 'type' parameter, they now both take a list of types in the 'types' argument.


0.2.10
-----
* Added task timeout control to simepleworkflow tasks.

0.2.9
-----
* Added multiplex input port support to simpleworkflow tasks.


0.2.8
-----
* Added ability to get events from simpleworkflows module: ```workflow.events```

0.2.7
-----
* Correct band ordering in the idaho leaflet map viewer
* Upgrade to gbdx-auth 0.1.3 which fixes a token refresh bug


0.2.6
-----

...
