# SLIM notes

## Getting started

1. Set environment variables:
    * `export JUPYTER_PASSWORD=<PASSWORD FOR JUPYTER AUTH>`
    * `export ODC_ACCESS_KEY=<AWS KEY ID>`
    * `export ODC_SECRET_KEY=<AWS KEY SECRET>`
2. Run the docker-compose workspace with `make up` or `docker-compose up`
3. Initialise the Open Data Cube database with `make initdb` (or see the Makefile for the command)
4. Add metadata with `make add-metadata`
5. Add product definitions with `make add-products`
6. Index data (needs AWS creds):
    * `make index-dlcd`
    * `make index-epi`
    * `make index-soil`
    * `make index-transport`
    * `make index-valuation`
    * `make index-valuation-pa`
    * `make index-dem`
    * `make index-dlcdnsw`

## Products
* `dem`:
  * NSW digital elevation model (5m state wide)
* `dlcd`:
  * Dynamic Land Cover Dataset Sydney only
* `dlcdnsw`:
  * Dynamic Land Cover Dataset whole of NSW 
* `epi`:
  * Environmentally Sensitive Land
  * Flood
  * Future Residential Growth Area
  * Heritage
* `soil`:
  * Acid
  * LSC OverMod
  * SoilMass
  * SoilSalinity
  * ShallowRock
  * Structure
  * WaterE
  * Waterlog
  * WindErosion
* `transport`:
  * Railway Station Proximity
  * Road Segment Proximity
* `valuation`:
  * Valuation 2013
  * Valuation 2014
  * Valuation 2015
  * Valuation 2016
  * Valuation 2017
  * Valuation pa 2013-17
