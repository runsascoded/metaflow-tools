ARG FROM_TAG=latest
FROM 386834949250.dkr.ecr.us-east-1.amazonaws.com/rightsize_02_conda37:$FROM_TAG

ENV CONDA_HOME="/opt/conda"
ENV PATH="$CONDA_HOME/bin:$PATH"

RUN conda install --yes \
    -c conda-forge \
    python==3.7 \
    python-blosc \
    prefect \
    cytoolz \
    dask==2.19.0 \
    lz4 \
    nomkl \
    numpy==1.18.1 \
    pandas==1.0.5 \
    tini==0.18.0 \
    && conda clean -tipsy \
    && find $CONDA_HOME/ -type f,l -name '*.a' -delete \
    && find $CONDA_HOME/ -type f,l -name '*.pyc' -delete \
    && find $CONDA_HOME/ -type f,l -name '*.js.map' -delete \
    && find $CONDA_HOME/lib/python*/site-packages/bokeh/server/static -type f,l -name '*.js' -not -name '*.min.js' -delete \
    && rm -rf $CONDA_HOME/pkgs

RUN conda install --yes \
    -c rapidsai \
    dask-cuda>=0.9.1

COPY rightsize_dask_prepare.sh /usr/bin/prepare.sh

RUN mkdir /opt/app

ENTRYPOINT ["tini", "-g", "--", "/usr/bin/prepare.sh"]
