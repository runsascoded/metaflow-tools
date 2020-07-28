ARG FROM_TAG=latest
FROM 386834949250.dkr.ecr.us-east-1.amazonaws.com/rightsize_01_base_cuda102_py37:$FROM_TAG

# See reference docker used by dask compose files
# https://github.com/ContinuumIO/docker-images/blob/master/miniconda3/debian/Dockerfile

RUN echo bb2e3cedd2e78a8bb6872ab3ab5b1266a90f8c7004a22d8dc2ea5effeb6a439a > expected_hash.txt && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    sha256sum < ~/miniconda.sh | cut -d\  -f1 > received_hash.txt

RUN if ! cmp --silent expected_hash.txt received_hash.txt; then \
      echo "Invalid miniconda installer"; \
      exit 1; \
    else \
        echo "miniconda installer is valid"; \
        rm expected_hash.txt received_hash.txt; \
    fi

RUN /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    /opt/conda/bin/conda clean -afy

ENV CONDA_PIP=/opt/conda/bin/pip

#RUN sh Miniconda3-latest-Linux-x86_64.sh -b
#RUN ~/miniconda3/bin/conda init
#RUN rm Miniconda3-latest-Linux-x86_64.sh




