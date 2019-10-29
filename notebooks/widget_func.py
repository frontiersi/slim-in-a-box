# Load modules
from ipyleaflet import (
    Map,
    GeoJSON,
    DrawControl,
    basemaps
)
import datetime as dt
import datacube
import ogr
import osr
import matplotlib as mpl
import matplotlib.pyplot as plt
import rasterio
from rasterio import features
import xarray as xr
from IPython.display import display
import warnings
import ipywidgets as widgets
import numpy as np

def transform_from_wgs_poly(geo_json,EPSGa):

    polygon = ogr.CreateGeometryFromJson(str(geo_json))

    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)

    target = osr.SpatialReference()
    target.ImportFromEPSG(EPSGa)

    transform = osr.CoordinateTransformation(source, target)
    polygon.Transform(transform)

    return polygon, eval(polygon.ExportToJson())

def run_valuation_app():
    """
    Description of function to come
    """
    # Suppress warnings
    warnings.filterwarnings('ignore')

    # Update plotting functionality through rcParams
    mpl.rcParams.update({'figure.autolayout': True})
    
    #Start the datacube
    dc = datacube.Datacube(app='dem')

    # Set the parameters to load the backgroun map
    # center specifies where the background map view should focus on
    # zoom specifies how zoomed in the background map should be
    loadeddata_center = [-31.840233, 145.612793]
    loadeddata_zoom = 5

    # define the background map
    studyarea_map = Map(
        center=loadeddata_center,
        zoom=loadeddata_zoom,
        basemap=basemaps.OpenStreetMap.Mapnik
    )

    # define the drawing controls
    studyarea_drawctrl = DrawControl(
        polygon={"shapeOptions": {"fillOpacity": 0}},
        marker={},
        circle={},
        circlemarker={},
        polyline={},
    )

    # add drawing controls and data bound geometry to the map
    studyarea_map.add_control(studyarea_drawctrl)
    #studyarea_map.add_layer(GeoJSON(data=geom_obj))

    # Index to count drawn polygons
    polygon_number = 0

    # Define widgets to interact with
    instruction = widgets.Output(layout={'border': '1px solid black'})
    with instruction:
        print("Draw a polygon within the red box to estimate "
              "the number of pixels in the polygon.")

    info = widgets.Output(layout={'border': '1px solid black'})
    with info:
        print("Plot status:")

    colour_list = plt.rcParams['axes.prop_cycle'].by_key()['color']

    # Function to execute each time something is drawn on the map
    def handle_draw(self, action, geo_json):
        nonlocal polygon_number

        # Execute behaviour based on what the user draws
        if geo_json['geometry']['type'] == 'Polygon':

            # Convert the drawn geometry to pixel coordinates
            geom_selectedarea_flat, geom_selectedarea = transform_from_wgs_poly(
                geo_json['geometry'],
                EPSGa=3577  # hard-coded to be same as case-study data
            )
            
            geom_envelope = geom_selectedarea_flat.GetEnvelope()
            minX, maxX, minY, maxY = geom_envelope
            
            # Insert dc.load for dem and dlcdnsw
            x_range = (minX, maxX)
            y_range = (minY, maxY)
            inputcrs = "EPSG:3577"
            resolution = (-5, 5)
            
            ds_dem = dc.load(
                product='dem',
                x=x_range,
                y=y_range,
                crs=inputcrs,
                output_crs=inputcrs,
                resolution=resolution,
                dask_chunks={'time': 1}
            )


            # Construct a mask to only select pixels within the drawn polygon
            mask = features.geometry_mask(
                [geom_selectedarea for geoms in [geom_selectedarea]],
                out_shape=ds_dem.geobox.shape,
                transform=ds_dem.geobox.affine,
                all_touched=False,
                invert=True
            )
            
            masked_ds = ds_dem.band1.where(mask)
            pixel_count = masked_ds.count()

            colour = colour_list[polygon_number % len(colour_list)]

            # Add a layer to the map to make the most recently drawn polygon
            # the same colour as the line on the plot
            studyarea_map.add_layer(
                GeoJSON(
                    data=geo_json,
                    style={
                        'color': colour,
                        'opacity': 1,
                        'weight': 4.5,
                        'fillOpacity': 0.0
                    }
                )
            )
            
            info.clear_output(wait=True)  # wait=True reduces flicker effect
            with info:
                print(ds_dem)
                print(masked_ds)

            # Iterate the polygon number before drawing another polygon
            polygon_number = polygon_number + 1

        else:
            info.clear_output(wait=True)
            with info:
                print("Plot status: this drawing tool is not currently "
                      "supported. Please use the polygon tool.")

    # call to say activate handle_draw function on draw
    studyarea_drawctrl.on_draw(handle_draw)

    # Construct UI:
    #  +-----------------------+
    #  | instruction           |
    #  +-----------+-----------+
    #  |  map                  |
    #  |                       |
    #  +-----------+-----------+
    #  | info                  |
    #  +-----------------------+
    ui = widgets.VBox([instruction,
                       studyarea_map,
                       info])
    display(ui)