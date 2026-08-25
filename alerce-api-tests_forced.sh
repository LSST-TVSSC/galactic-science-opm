#!/bin/bash

PAYLOAD=$(jq -n \
  '{
    classifier:"lc_classifier_BHRF_forced_phot",
    class_name:"Microlensing",
    format:"pandas",
    firstmjd:61241.19212959986,
    page:0,
    order_by:"probability",
    order_mode:"DESC",
    survey: "ztf"
  }')

curl  -G -L https://api.alerce.online/v2/lightcurve/forced-photometry/ZTF26abdgtui -vvv \
      -d "format=pandas" | jq '.' > response_forced.json


