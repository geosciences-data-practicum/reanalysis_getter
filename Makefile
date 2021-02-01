# Makefile to make execution easier
.PHONY: create-image run_jupyter
PWD=${pwd}
CONTAINER_NAME="jetstream_container.sing"
DATA_FOLDER="/project2/moyer/jetstream"
PORT=2500

IP = $(shell /sbin/ip route get 8.8.8.8 | head -n 1 | awk '{print $$NF}' )

container:
	module load singularity ; \
        echo "Bulding ${CONTAINER_NAME} image in /images " ; \
	mkdir images ; \
	singularity build --remote --force images/${CONTAINER_NAME} infrastructure/conda_environment_jetstream.def

run-jupyter:
	module load singularity ; \
	echo "Loading notebook" ; \
	singularity exec --bind "${DATA_FOLDER}:${DATA_FOLDER}":ro images/${CONTAINER_NAME} infrastructure/run_in_singularity.sh -n ${IP} ${PORT}

images:
	mkdir images

clean:
	rm -r images ; \
	rm -r build ; \
	rm -r dist ; \
	rm -r dask-worker-space
