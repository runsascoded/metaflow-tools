ARG FROM_TAG=latest
FROM 386834949250.dkr.ecr.us-east-1.amazonaws.com/rightsize_03_dask_base_py37:$FROM_TAG

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

RUN rm -rf /tmp/* \
    && apt-get clean \
    && apt-get update

RUN groupadd -g 3000 celsiustx \
    && groupadd --gid 2000 --force sharedproject_users \
    && useradd -m -u 3000 -g celsiustx celsiustx \
    && usermod -aG  sharedproject_users celsiustx \
    && echo 'celsiustx ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers.d/90-rightsize \
    && chmod 440 "/etc/sudoers.d/90-rightsize"

# If this is used for prefect, the celsius user will need access to the /opt directory
RUN mkdir -p /opt/prefect && chown celsiustx /opt/prefect
USER celsiustx
WORKDIR /home/celsiustx
ENV HOME="/home/celsiustx"
ENV CTX_HOME=$HOME

COPY private-deps/scannotate/requirements.txt ./scannotate.requirements.txt
COPY private-deps/tumortate/requirements.txt ./tumortate.requirements.txt
COPY private-deps/phenograph/requirements.txt ./phenograph.requirements.txt
COPY private-deps/palantir/requirements.txt ./palantir.requirements.txt

RUN $CONDA_PIP install --user --no-warn-script-location -r scannotate.requirements.txt \
    && $CONDA_PIP install --user --no-warn-script-location -r tumortate.requirements.txt \
    && $CONDA_PIP install --user --no-warn-script-location -r phenograph.requirements.txt \
    && $CONDA_PIP install --user --no-warn-script-location -r palantir.requirements.txt

COPY private-deps/scannotate/scannotate ./scannotate
COPY private-deps/tumortate/tumortate ./tumortate
COPY private-deps/phenograph/phenograph ./phenograph
# TODO - why in src?
COPY private-deps/palantir/src/palantir ./palantir

# Keep this at the end, as it is where most of the changes will happen
COPY private-deps/celsius-utils/requirements.txt ./celsius-utils.requirements.txt
COPY private-deps/ctxbio/requirements.txt ./ctxbio.requirements.txt
COPY private-deps/cesium3/client/requirements.txt cesium3-requirements.txt
COPY private-deps/multisample-analysis/requirements.txt ./multisample-analysis.requirements.txt

RUN $CONDA_PIP install --user --no-warn-script-location -r celsius-utils.requirements.txt \
    && $CONDA_PIP install --user --no-warn-script-location -r ctxbio.requirements.txt \
    && $CONDA_PIP install --user --no-warn-script-location -r cesium3-requirements.txt \
    && $CONDA_PIP install --user --no-warn-script-location -r multisample-analysis.requirements.txt

COPY private-deps/celsius-utils/ctxcommon ./ctxcommon
COPY private-deps/ctxbio/ctxbio ./ctxbio
COPY  --chown=celsiustx:celsiustx private-deps/ctxbio/test ./ctxbio/test
COPY private-deps/cesium3/client/celsiustx ./celsiustx

COPY private-deps/multisample-analysis/infrastructure ./infrastructure
COPY private-deps/multisample-analysis/sc_analysis ./sc_analysis
COPY private-deps/multisample-analysis/scripts ./scripts
COPY --chown=celsiustx private-deps/multisample-analysis/test ./test

COPY private-deps/rightsize/requirements.txt ./rightsize.requirements.txt
RUN $CONDA_PIP install --user --no-warn-script-location -r rightsize.requirements.txt

COPY private-deps/prefect ./prefect
COPY private-deps/rightsize/rightsize ./rightsize

ENV PATH="${HOME}/.local/bin:${PATH}"
ENV PYTHONPATH "${PYTHONPATH}:${HOME}:prefect/server/src"

RUN jupyter contrib nbextension install --user

# See http://numba.pydata.org/numba-doc/latest/user/parallel.html#diagnostics
# and http://numba.pydata.org/numba-doc/latest/reference/envvars.html#envvar-NUMBA_PARALLEL_DIAGNOSTICS
ENV NUMBA_PARALLEL_DIAGNOSTICS=4

# Patches
#COPY private-deps/rightsize/infrastructure/patch/execute.py .local/lib/python3.7/site-packages/prefect/cli/execute.py
#COPY private-deps/rightsize/infrastructure/patch/s3.py .local/lib/python3.7/site-packages/prefect/environments/storage/s3.py

#ENTRYPOINT ["python3", "-u", "-m", "infrastructure.docker.msa_entrypoint_wrapper"]


