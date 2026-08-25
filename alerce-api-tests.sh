#!/bin/bash

PAYLOAD=$(jq -n \
  '{
    classifier:"lc_classifier_BHRF_forced_phot",
    class_name:"Microlensing",
    format:"pandas",
    firstmjd:61230.350879599806,
    page:0,
    order_by:"probability",
    order_mode:"DESC",
    survey: "ztf"
  }')

curl  -G -L https://api.alerce.online/ztf/v1/objects -vvv \
      -d "classifier=lc_classifier_BHRF_forced_phot" \
      -d "class=Microlensing" \
      -d "firstmjd=61200.19212959986" \
      -d "page=0" \
      -d "page_size=250" \
      -d "order_by=probability" \
      -d "order_mode=DESC" \
      -d "survey=ztf" | jq '.' > response_objects.json


