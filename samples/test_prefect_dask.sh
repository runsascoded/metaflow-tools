#!/bin/bash
export PREFECT__ENGINE__EXECUTOR__DEFAULT_CLASS="prefect.engine.executors.DaskExecutor"
export PREFECT__ENGINE__EXECUTOR__DASK__ADDRESS="tcp://0.0.0.0:18786"
# export PREFECT__ENGINE__EXECUTOR__DASK__ADDRESS="tcp://0.0.0.0:4200"
python3 prefect_hello.py

