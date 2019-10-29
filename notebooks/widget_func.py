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
import pandas as pd

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
    loadeddata_center = [-33.419474, 149.577299]
    loadeddata_zoom = 12

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
        
    fig_display = widgets.Output(layout=widgets.Layout(
        width="50%",  # proportion of horizontal space taken by plot
    ))

    with fig_display:
        plt.ioff()
        fig, ax = plt.subplots(figsize=(8, 6))

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
            dem_res = (-5, 5)
            dlcd_res = (-100, 100)
            
            ds_dem = dc.load(
                product='dem',
                x=x_range,
                y=y_range,
                crs=inputcrs,
                output_crs=inputcrs,
                resolution=dem_res,
                dask_chunks={'time': 1}
            )
            
            ds_dlcd = dc.load(
                product='dlcdnsw',
                x=x_range,
                y=y_range,
                crs=inputcrs,
                output_crs=inputcrs,
                resolution=dlcd_res,
                dask_chunks={'time': 1}
            )
            
            # Load DLCD land cover look-up table
            dlcd_lookup = pd.read_csv("dlcd.csv")
            
            # Construct a mask to only select pixels within the drawn polygon
            mask_dem = features.geometry_mask(
                [geom_selectedarea for geoms in [geom_selectedarea]],
                out_shape=ds_dem.geobox.shape,
                transform=ds_dem.geobox.affine,
                all_touched=False,
                invert=True
            )
            
            mask_dlcd = features.geometry_mask(
                [geom_selectedarea for geoms in [geom_selectedarea]],
                out_shape=ds_dlcd.geobox.shape,
                transform=ds_dlcd.geobox.affine,
                all_touched=False,
                invert=True
            )
            
            
            # Apply the mask to the loaded data
            masked_dem = ds_dem.band1.where(mask_dem)
            masked_dlcd = ds_dlcd.band1.where(mask_dlcd)
            
            # Compute the total number of pixels in the masked data set
            pix_dem = masked_dem.count().compute().item()
            pix_dlcd = masked_dlcd.count().compute().item()
            
            # Convert dlcd to pandas and get value counts for each class
            pd_dlcd = ds_dlcd.to_dataframe()
            pd_dlcd_classcount = pd_dlcd.band1.value_counts().reset_index(name='counts')
            
            # Join dlcd counts against landcover look up table
            pd_dlcd_coverage = pd.merge(pd_dlcd_classcount, dlcd_lookup, how="left", left_on=['index'], right_on=['id'])
            
            # Format the counts table to keep necessary items
            pd_dlcd_coverage['area(km^2)'] = pd_dlcd_coverage['counts'] * (dlcd_res[1]/1000.)**2
            pd_dlcd_coverage['percentage_area'] = pd_dlcd_coverage['counts']/pd_dlcd_coverage['counts'].sum()*100
            
            pd_dlcd_output = pd_dlcd_coverage[['Name', 'area(km^2)', 'percentage_area']]
            
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
            
            # Make the DLDC Summary plot
            ax.clear()
            pd_dlcd_output.plot.bar(x='Name', y='percentage_area', rot=45, ax=ax, legend=False, color=colour)
            ax.set_xlabel("Land Cover Class")
            ax.set_ylabel("Percentage Coverage Of Polygon")
            
            # refresh display
            fig_display.clear_output(wait=True)  # wait=True reduces flicker effect
            with fig_display:
                display(fig)
            
            info.clear_output(wait=True)  # wait=True reduces flicker effect
            with info:
                print(pd_dlcd_output)

            # Iterate the polygon number before drawing another polygon
            polygon_number = polygon_number + 1

        else:
            info.clear_output(wait=True)
            with info:
                print("Plot status: this drawing tool is not currently "
                      "supported. Please use the polygon tool.")

    # call to say activate handle_draw function on draw
    studyarea_drawctrl.on_draw(handle_draw)
    
    with fig_display:
        # TODO: update with user friendly something
        display(widgets.HTML(""))

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
                       widgets.HBox([studyarea_map, fig_display]),
                       info])
    display(ui)