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
from pyproj import Proj, transform

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

def build_metadata(bucket, file_path, product_type):
    s3_path_template = "s3://{bucket}/{file}"

    s3_path = s3_path_template.format(
        bucket=bucket,
        file=file_path
    )
    raster = rasterio.open(s3_path)
    bounds = raster.bounds
    crs_code = raster.crs.to_epsg()

    # Nasty hack, but RasterIO can't find the EPSG code sometimes...
    if crs_code is None:
        crs_code = '3308'
    crs_string = 'epsg:{}'.format(crs_code)

    # Handle dates
    dates = year_re.findall(file_path)

    year = '2018'
    from_date = datetime.datetime(year=int(year), month=1, day=1)
    to_date = from_date

    if len(dates) > 0:
        from_date = datetime.datetime(year=int(dates[0]), month=1, day=1)
        if len(dates) > 1:
            to_date = datetime.datetime(year=int(dates[1]), month=1, day=1)
    
    centre_date = from_date

    # Handle coordinates
    top = bounds.top
    bottom = bounds.bottom
    right = bounds.right
    left = bounds.left

    # Get some WGS lat/lon
    inProj = Proj(init=crs_string)
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

    return docdict


def index_dataset(dataset_dict, s3_path):
    dc = datacube.Datacube()
    index = dc.index
    resolver = Doc2Dataset(index)
    dataset, err  = resolver(dataset_dict, s3_path)
    if err is not None:
        logging.error("%s", err)
    else:
        try:
            index.datasets.add(dataset)
        except changes.DocumentMismatchError as e:
            index.datasets.update(dataset, {tuple(): changes.allow_any})
        except Exception as e:
            err = e
            logging.error("Unhandled exception {}".format(e))

    return dataset, err


@click.command(help= "Enter Bucket name and other parameters")
@click.argument('bucket')
@click.option('--path', '-p', help="Pass the prefix of the object to the bucket")
@click.option('--extension', '-e', help="Pass extension to filter on")
@click.option('--product_type', '-t', help="The product type, or name for the product")
def do_work(bucket, path, extension, product_type):
    count = 0
    limit = None
    # List the bucket and get all the files with the extension we want
    files = get_matching_s3_keys(bucket, prefix=path, suffix=extension)

    for s3_path in files:
        if limit and count >= limit:
            logging.warning("Finished processing {}, which is the limit".format(count))
            return
        logging.info("Working on {}".format(s3_path))

        dataset_dict = build_metadata(bucket, s3_path, product_type)

        index_dataset(dataset_dict, s3_path)
        count += 1

if __name__ == "__main__":
    logging.info("Script is starting up")
    # 'test.data.frontiersi.io', 'temp', 'tif', 'dlcd'
    do_work()
    logging.info("Script ends")
