#!/usr/bin/env python3

import datetime
import logging
import re
import uuid

import boto3
import click
import datacube
import rasterio
from datacube.index.hl import Doc2Dataset
from datacube.utils import changes
from pyproj import Proj, transform, CRS

# Set us up some logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('s3transfer').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# BUCKET = 'test.data.frontiersi.io'
# PATH = 'temp'
# EXTENSION = 'tif'
# PRODUCT_TYPE = 'dlcd'

OVERWRITE = True

year_re = re.compile(r'([2][0-9]{3})')


def get_matching_s3_keys(bucket, prefix='', suffix=''):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    s3 = boto3.client('s3')

    kwargs = {'Bucket': bucket, 'Prefix': prefix}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        if not resp.get('Contents'):
            logging.warning("No keys found at {}/{} with the suffix {}".format(
                bucket, prefix, suffix
            ))
            return None
        for obj in resp['Contents']:
            key = obj['Key']
            if key.endswith(suffix):
                yield key
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break


def do_work(bucket, path, extension, product_type):
    count = 0
    #limit = None
    # List the bucket and get all the files with the extension we want
    files = get_matching_s3_keys(bucket, prefix=path, suffix=extension)

    s3_path_template = "s3://{bucket}/{file}"

    for s3_path in files:
        full_path = f"s3://{bucket}/{s3_path}"

        # Generate raster from file path
        raster = rasterio.open(full_path)

        # Extract bounds and crs
        bounds = raster.bounds
        crs_code = raster.crs.to_wkt()

        # hardcode date
        to_date = datetime.datetime(year=2018, month=1, day=1)
        from_date = datetime.datetime(year=2018, month=1, day=1)
        centre_date = datetime.datetime(year=2018, month=1, day=1)

        # Handle coordinates
        top = bounds.top
        bottom = bounds.bottom
        right = bounds.right
        left = bounds.left

        inProj = Proj(CRS.from_string(crs_code))
        outProj = Proj(init='epsg:4326')
        left_ll, bottom_ll = transform(inProj, outProj, left, bottom)
        right_ll, top_ll = transform(inProj, outProj, right, top)

        # unprojected
        coordinates = {
            'ul':
                {'lon': left_ll, 'lat': top_ll},
            'ur':
                {'lon': right_ll, 'lat': top_ll},
            'lr':
                {'lon': right_ll, 'lat': bottom_ll},
            'll':
                {'lon': left_ll, 'lat': bottom_ll}
        }

        # projected
        geo_ref_points = {
            'ul':
                {'x': left, 'y': top},
            'ur':
                {'x': right, 'y': top},
            'lr':
                {'x': right, 'y': bottom},
            'll':
                {'x': left, 'y': bottom}
        }

        docdict = {
            'id': str(uuid.uuid5(uuid.NAMESPACE_URL, s3_path)),
            'product_type': product_type,
            'creation_dt': centre_date,
            'platform': {'code': 'slim'},
            'instrument': {'name': 'slim'},
            'extent': {
                'from_dt': from_date,
                'to_dt': to_date,
                'center_dt': centre_date,
                'coord': coordinates,
            },
            'format': {'name': 'GeoTiff'},
            'grid_spatial': {
                'projection': {
                    'geo_ref_points': geo_ref_points,
                    'spatial_reference': crs_string,
                }
            },
            'image': {
                'bands': {
                    'band1': {
                        'path': s3_path,
                        'layer': 1,
                    }
                }
            },

            'lineage': {'source_datasets': {}}
        }

        print (docdict)
    # for s3_path in files:
    #     if limit and count >= limit:
    #         logging.warning(
    #             "Finished processing {}, which is the limit".format(count))
    #         return
    #     logging.info("Working on {}".format(s3_path))
    #
    #     dataset_dict = build_metadata(bucket, s3_path, product_type)
    #
    #     index_dataset(dataset_dict, s3_path)
    #     count += 1

if __name__ == "__main__":
    logging.info("Script is starting up")
    # 'test.data.frontiersi.io', 'nsw-dem/elevation/elvis', 'tif', 'dem'
    do_work('test.data.frontiersi.io', 'nsw-dem/elevation/mapsheet', '.tif', 'dem')
    logging.info("Script ends")
