# SLIM notes

## Getting started

1. Run the docker-compose workspace with `make up` or `docker-compose up`
2. Initialise the Open Data Cube database with `make initdb` (or see the Makefile for the command)
3. Add metadata with `make add-metadata`
4. Add product definitions with `make add-products`
5. Index data (needs AWS creds):
    * `make index-dlcd`
    * `make index-epi`
    * `make index-soil`
    * `make index-transport`
    * `make index-valuation`
    * `make index-valuation-pa`.

## Products
* `dlcd`: 
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
