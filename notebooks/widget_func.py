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


def get_slope(dem, *resolution):
    x, y = np.gradient(dem, *resolution)

    slope = np.arctan(np.sqrt(x*x + y*y)) * 180 / np.pi
    xr_slope = xr.full_like(dem, slope)
    return xr_slope


def slope_category(slope_degrees):
    if np.isnan(slope_degrees):
        return np.nan
    if slope_degrees < 5:
        return 0
    if slope_degrees < 11:
        return 1
    if slope_degrees < 18:
        return 2
    if slope_degrees < 26:
        return 3
    if slope_degrees < 35:
        return 4
    return 5


def unique_counts(dataset):
    stacked_array = dataset.to_array().values
    flat_array = np.reshape(stacked_array, (stacked_array.shape[0], -1))

    unique_keys, counts = np.unique(flat_array, axis=1, return_counts=True)
    valid_keys = np.isfinite(unique_keys).all(axis=0)
    unique_keys, counts = unique_keys[:, valid_keys].astype(np.int16), counts[valid_keys]

    coords = {name: ('value', vals) for name, vals in zip(dataset, unique_keys)}
    return xr.Dataset(data_vars={'count': ('value', counts)}, coords=coords)['count']


def get_slope_raster(dc, x_range, y_range, inputcrs, resolution, geom_selectedarea):
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
    mask_dem = features.geometry_mask(
        [geom_selectedarea for geoms in [geom_selectedarea]],
        out_shape=ds_dem.geobox.shape,
        transform=ds_dem.geobox.affine,
        all_touched=False,
        invert=True
    )

    # Calculate Slope category
    slope = get_slope(ds_dem.band1.squeeze('time', drop=True), *resolution).where(mask_dem)
    slope_cat = xr.apply_ufunc(slope_category, slope, vectorize=True, dask='parallelized', output_dtypes=[np.float32])
    slope_cat.name = 'slope_category'

    return slope_cat


def get_dlcd_raster(dc, x_range, y_range, inputcrs, resolution, geom_selectedarea):
    """

    :param x_range: tuple() of x values
    :param y_range: tuple of y values
    :param inputcrs: crs of x and y values
    :param resolution:
    :param geom_selectedarea:
    :return:
    """
    ds_dlcd = dc.load(
        product='dlcdnsw',
        x=x_range,
        y=y_range,
        crs=inputcrs,
        output_crs=inputcrs,
        resolution=resolution,
        dask_chunks={'time': 1}
    )

    mask_dlcd = features.geometry_mask(
        [geom_selectedarea for geoms in [geom_selectedarea]],
        out_shape=ds_dlcd.geobox.shape,
        transform=ds_dlcd.geobox.affine,
        all_touched=False,
        invert=True
    )

    masked_dlcd = ds_dlcd.band1.where(mask_dlcd)
    masked_dlcd.name = 'dlcd'
    return masked_dlcd


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
            # dlcd_res is unused as the same res must be used when loading
            # multiple products (to support the cross count process). The
            # smallest cell size is used as this will provide the greatest
            # accuracy.
            dlcd_res = (-100, 100)  # unused

            slope_cat = get_slope_raster(dc, x_range, y_range, inputcrs, dem_res, geom_selectedarea)
            dlcd = get_dlcd_raster(dc, x_range, y_range, inputcrs, dem_res, geom_selectedarea)

            stacked = xr.merge([dlcd, slope_cat])
            cross_counts = unique_counts(stacked)

            slope_cat_count = slope_cat.to_dataframe().slope_category.value_counts().rename('counts').to_frame()
            slope_cat_count.index.name = 'index'
            slope_cat_table = pd.read_csv('slope_cat.csv')
            slope_coverage = pd.merge(slope_cat_count, slope_cat_table, how="left", left_on=['index'], right_on=['id'])

            # Compute the total number of pixels in the masked data set
            pix_dlcd = dlcd.count().compute().item()

            # Convert dlcd to pandas and get value counts for each class
            pd_dlcd = dlcd.to_dataframe()
            pd_dlcd_classcount = pd_dlcd.dlcd.value_counts().reset_index(name='counts')

            # Convert slope_cat to pandas and get value counts for each category
            # pd_slope_cat_count = slope_cat.to_dataframe().band1.value_counts()

            # Load DLCD land cover look-up table
            dlcd_lookup = pd.read_csv("dlcd.csv")

            # Join dlcd counts against landcover look up table
            pd_dlcd_coverage = pd.merge(pd_dlcd_classcount, dlcd_lookup, how="left", left_on=['index'], right_on=['id'])

            # Format the counts table to keep necessary items
            pd_dlcd_coverage['area(km^2)'] = pd_dlcd_coverage['counts'] * (dem_res[1]/1000.)**2
            pd_dlcd_coverage['percentage_area'] = pd_dlcd_coverage['counts']/pd_dlcd_coverage['counts'].sum()*100

            pd_dlcd_output = pd_dlcd_coverage[['Name', 'area(km^2)', 'percentage_area']]

            # manipulate cross counts into format suitable for presentation as
            # a table
            pd_cross_counts = cross_counts.to_dataframe()
            pd_cross_counts.sort_values(
                by='count', ascending=False, inplace=True)
            # join DLCD lookup table for DLCD class names
            pd_cross_counts = pd.merge(
                pd_cross_counts, dlcd_lookup, how='left', left_on=['dlcd'],
                right_on=['id'])
            pd_cross_counts = pd_cross_counts.rename(
                columns={'dlcd': 'dlcd_id', 'Name': 'DLCD'})
            # join slope category definition table for slope class names
            pd_cross_counts = pd.merge(
                pd_cross_counts, slope_cat_table, how='left',
                left_on=['slope_category'], right_on=['id'])
            pd_cross_counts['slope'] = (
                pd_cross_counts[['label', 'range']].apply(
                    lambda x: '{} {}'.format(x[0], x[1]), axis=1))

            # Format the counts table to keep necessary items
            pd_cross_counts['area(km^2)'] = (
                pd_cross_counts['count'] * (dem_res[1]/1000.)**2)
            pd_cross_counts['percentage_area'] = (
                pd_cross_counts['count']/pd_cross_counts['count'].sum()*100)

            pd_cross_counts_output = (
                pd_cross_counts[
                    ['DLCD', 'slope', 'area(km^2)', 'percentage_area']])

            # display(pd_cross_counts)

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
                # use to_string function to avoid truncation of results
                print(pd_cross_counts_output.to_string())

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
