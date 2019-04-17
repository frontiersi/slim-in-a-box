# Non docker-compose deployments
Rough notes on the deployment steps required for non docker-compose environments (eg; those not supported by the makefile)

## General ODC commands

Initialise ODC, and add metadata/product definitions
```
datacube -v system init
datacube metadata_type add /scripts/slim-metadata.yaml
datacube product add /scripts/slim-products.yaml
```

Indexing SLIM data located in S3 bucket
```
python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/dlcd \
            -e tif \
            -t dlcd

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/epi \
            -e EPIEnvironmentallySensitiveLand.shp_cut.tif \
            -t esl

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/epi \
            -e EPIFutureResidentialGrowthArea.shp_cut.tif \
            -t frga

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/epi \
            -e EPIHeritageHER.shp_cut.tif \
            -t her

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/epi \
            -e EPIFlood.shp_cut.tif \
            -t flood

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilAcid.shp_cut.tif \
            -t acid

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilMass_m.shp_cut.tif \
            -t mass

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilLSC_OverMod.shp_cut.tif \
            -t lsc_overmod

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilSalinity.shp_cut.tif \
            -t salinity

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilShallowRock.shp_cut.tif \
            -t shallow_rock

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilStructure.shp_cut.tif \
            -t structure

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilWaterE.shp_cut.tif \
            -t water

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilWaterlog.shp_cut.tif \
            -t waterlog

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/soil \
            -e SoilWindErosion.shp_cut.tif \
            -t wind_erosion

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/transport \
            -e railwaystation.shp_proximity_cut.tif \
            -t rail

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/transport \
            -e roadsegment.shp_proximity_cut.tif \
            -t road

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/valuation/ \
            -e tif \
            -t valuation

python3 index-cogs-live.py \
            test.data.frontiersi.io \
            -p slim-odc-datasets/valuation_pa/ \
            -e tif \
            -t valuation_pa
```

If required the product definition can be updated as follows.
```
datacube -v product update --allow-unsafe slim-products.yaml
```
