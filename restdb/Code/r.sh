#!/bin/sh
while true 
do

	killall -9 python
	python main.py -d &

	sleep 10

done
