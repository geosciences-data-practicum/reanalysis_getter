#!/usr/bin/env bash

#############################################
# JUPYTER WRAPPER FOR SINGULARITY CONTAINER #
############################################# 

IP=$2
PORT=$3

export PATH="/opt/conda/envs/integration_env/bin:${PATH}"
. /opt/conda/etc/profile.d/conda.sh
conda activate pangeo


function re-build-env () { 
    . /opt/conda/etc/profile.d/conda.sh
    conda activate pangeo
    # Install scc_multiverse library
    if [[ -e requirements/requirements.txt ]] 
    then
    	pip install -r requirements/requirements.txt
    	pip install -e .
    else
    	pip install -e .
    fi
}

function ganymede () {
    conda activate pangeo
    jupyter-lab --no-browser --ip $IP --port $PORT --allow-root 

}

function help_menu () {
cat << EOF
Usage: ${0} {build|notebook}
OPTIONS:
   -h|help             Show this message
   -b|--build
   -n|--notebook
INFRASTRUCTURE:
   Build the infrastructure and output python:
        $ ./run_singularity.sh --build
   Run notebook inside Singularity image. This function takes arguments
   for both IP and port to use in Jupyterlab
	$ ./run_singularity.sh --notebook 0.0.0.0 8888
EOF
}

if [[ $# -eq 0 ]] ; then
	help_menu
	exit 0
fi

case "$1" in
    -b|--build)
        re-build-env
	shift
        ;;
    -n|--notebook)
	re-build-env
        ganymede
	shift
        ;;
   *)
       echo "${1} is not a valid flag, try running: ${0} --help"
       ;;
esac
shift
