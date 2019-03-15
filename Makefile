# Start it up
up:
	docker-compose up

# Get it prepared
initdb:
	docker-compose exec jupyter datacube -v system init

# Some extra commands to help in managing things
# Rebuild the image
build:
	docker-compose build

# Start an interactive shell
shell:
	docker-compose exec jupyter bash

# Delete everything
clear:
	docker-compose stop
	docker-compose rm -fs

# Get example data
get-sample-data:
	aws s3 cp s3://test.data.frontiersi.io/slim-odc-datasets/dlcd/DLCD_v2-1_MODIS_EVI_10_20110101-20121231_cut.tif data/
	aws s3 cp s3://test.data.frontiersi.io/slim-odc-datasets/epi/EPIEnvironmentallySensitiveLand.shp_cut.tif data/
	aws s3 cp s3://test.data.frontiersi.io/slim-odc-datasets/transport/railwaystation.shp_proximity_cut.tif data/
	aws s3 cp s3://test.data.frontiersi.io/slim-odc-datasets/valuation/landValuation_2013.tif data/

create: initdb add-metadata add-products

add-metadata:
		docker-compose exec jupyter \
			datacube metadata_type add \
			/opt/odc/scripts/slim-metadata.yaml

add-products:
	docker-compose exec jupyter \
		datacube product add \
		/opt/odc/scripts/slim-products.yaml

index-dlcd:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/dlcd \
			-e tif \
			-t dlcd"

index-esl:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/epi \
			-e EPIEnvironmentallySensitiveLand.shp_cut.tif \
			-t esl"
