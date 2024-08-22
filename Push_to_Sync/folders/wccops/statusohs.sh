#!/bin/bash
pid=$(ps -ef | grep ohs | grep -v statusohs | grep -v grep | wc -l)

if [[ $pid != 0 ]]
then
        echo "OHS is running"
else
        echo "OHS is not running"
fi
