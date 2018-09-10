#!/bin/bash

root=$1

cd $root

while true
do
    python -i -m integrations.tim.fit.v1.services.partner
    sleep 60
done
