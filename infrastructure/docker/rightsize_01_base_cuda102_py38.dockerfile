#FROM nvcr.io/nvidia/tensorflow:19.05-py2
FROM nvidia/cuda:10.2-base


RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa

# Baseline,probably never changes
RUN apt-get update && \
    apt-get install -y \
        tree \
        unzip \
        lsof \
        wget \
        curl \
        sudo

# Development related systems
RUN apt-get install -y \
        build-essential \
        cmake \
        libboost-all-dev \
        libbz2-dev \
        libcurl3-dev \
        libffi-dev \
        liblzma-dev \
        libncurses5-dev \
        libssl-dev \
        zlib1g-dev

RUN apt-get install -y \
        python3.8 \
        python3.8-dev \
        python3-pip

WORKDIR ..

# Switch the system to use python3.6 by default - 2 is better than 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools

# Simple default command to dump GPU related details.  This will only work with a docker driver of nvidia-docker
#CMD ["sh","-c","nvidia-smi"]

