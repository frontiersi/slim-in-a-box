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
		datacube metadata add \
		/opt/odc/scripts/slim-metadata.yaml

add-products:
	docker-compose exec jupyter \
		datacube product add \
		/opt/odc/scripts/slim-products.yaml

index-dlcd:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/dlcd/ \
			-e tif \
			-t dlcd"

index-epi:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/epi \
			-e EPIEnvironmentallySensitiveLand.shp_cut.tif \
			-t esl"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/epi \
			-e EPIFutureResidentialGrowthArea.shp_cut.tif \
			-t frga"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/epi \
			-e EPIHeritageHER.shp_cut.tif \
			-t her"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/epi \
			-e EPIFlood.shp_cut.tif \
			-t flood"

index-soil:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilAcid.shp_cut.tif \
			-t acid"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilMass_m.shp_cut.tif \
			-t mass"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilLSC_OverMod.shp_cut.tif \
			-t lsc_overmod"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilSalinity.shp_cut.tif \
			-t salinity"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilShallowRock.shp_cut.tif \
			-t shallow_rock"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilStructure.shp_cut.tif \
			-t structure"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilWaterE.shp_cut.tif \
			-t water"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilWaterlog.shp_cut.tif \
			-t waterlog"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/soil \
			-e SoilWindErosion.shp_cut.tif \
			-t wind_erosion"

index-transport:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/transport \
			-e railwaystation.shp_proximity_cut.tif \
			-t rail"

	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/transport \
			-e roadsegment.shp_proximity_cut.tif \
			-t road"

index-valuation:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/valuation/ \
			-e tif \
			-t valuation"

index-valuation-pa:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/valuation_pa/ \
			-e tif \
			-t valuation_pa"

index-dem:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-dem.py"


index-dlcdnsw:
	docker-compose exec jupyter bash -c \
		"cd /opt/odc/scripts && python3 index-cogs-live.py \
			test.data.frontiersi.io \
			-p slim-odc-datasets/dlcd-nsw \
			-e tif \
			-t dlcdnsw"

