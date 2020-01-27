#!/usr/bin/env bash

source env/.project_env

# Exit the script as soon as something fails (-e) or if a variable is 
# not defined (-u)
set -e -u

# Run Jupyter Notebook within RCC's fancy environment

cat << "EOF"
______  _____  _____     ___                   _            
| ___ \/  __ \/  __ \   |_  |                 | |           
| |_/ /| /  \/| /  \/     | |_   _ _ __  _   _| |_ ___ _ __ 
|    / | |    | |         | | | | | '_ \| | | | __/ _ \ '__|
| |\ \ | \__/\| \__/\ /\__/ / |_| | |_) | |_| | ||  __/ |   
\_| \_| \____/ \____/ \____/ \__,_| .__/ \__, |\__\___|_|   
                                  | |     __/ |             
                                  |_|    |___/              
   __________             ______________
  |:""""""""i:           | ............ :
  |:        |:           | :          | :
  |: >boba  |:           | :          | :
  |:________!:           | :>@wwa.com | :
  |   .....  :---_____---| :__________! :
  |  '-----" :           |..............:
  | @        :"-__-_     |"""""""""""""":
  |..........:    _-"    |..............:
  /.::::::::.\   /\      /.::::::::.:::.\
 /____________\ (__)    /________________\
EOF


function print-env () {
        echo "###########################################"
        echo "##    Project Environment Information    ##"
        echo "###########################################"
        echo "Environment name: ${ENV_NAME}"
        echo "Data folder: ${DATA_FOLDER}"
        echo "Project repo root: ${ROOT_FOLDER}"

}


function build-env () {

    set +u

    module load Anaconda3
    ENV=$(conda env list | grep ${ENV_NAME} | wc -l)
    
    if [[ $ENV -eq 1 ]]
    then 
        echo "${ENV_NAME} is already created. I will just loaded it"
        #eval "$(conda shell.bash hook)" >> /dev/null

        echo "Now activate ${ENV_NAME}"
        CONDA_BASE=$(conda info --base)
        source $CONDA_BASE/etc/profile.d/conda.sh
        conda activate ${ENV_NAME}
    else
        conda env create -f ${ROOT_FOLDER}/env/environment.yml
        eval "$(conda shell.bash hook)"
        conda activate ${ENV_NAME}
    fi    
}


function ganymede () {
    
    IP=$(/sbin/ip route get 8.8.8.8 | head -n 1 | awk '{print $NF}')

    module load Anaconda3
    jupyter notebook --no-browser --port=${PORT} --ip $IP

}

function help_menu () {
cat << EOF
Usage: ${0} (-h | -i | -b | -r |)
OPTIONS:
   -h|--help                   Show this message
   -i|--info                   Show information about the environment
   -b|--build-conda-env        Build the conda ${ENV_NAME} 
   -r|--run-jupyter-env        Run Jupyter Notebook in the environment

EXAMPLES:
   Activate RCC Anaconda module and install conda env:
        $ ./load_stuff.sh -b
   Activaate and run a Jupyter notebook in local note:
        $ ./load_stuff.sh -r
EOF
}


if [[ $# -eq 0 ]] ; then
    help_menu
    exit 0
fi


# Deal with command-line flags

case "${1}" in 
    -b|--build-conda-env)
        build-env
        shift
        ;;
    -r|--run-jupyter-env)
        build-env
        ganymede
        shift
        ;;
     -i|--info)
         print-env
         shift
         ;;
    -h|--help)
        help_menu
        shift
        ;;
    *)
        echo "${1} is not a valid flag, try running: ${0} --help"
        ;;
esac 
shift
