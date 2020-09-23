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
        bzip2 \
        ca-certificates \
        cmake \
        git \
        libboost-all-dev \
        libbz2-dev \
        libcurl3-dev \
        libffi-dev \
        liblzma-dev \
        libncurses5-dev \
        libssl-dev \
        libxml2 \
        libxml2-dev \
        libxml2-utils \
        vim \
        zlib1g-dev

#    apt-get install -y wget bzip2 ca-certificates libglib2.0-0 libxext6 libsm6 libxrender1 git mercurial subversion && \

RUN apt-get install -y \
        python3.7 \
        python3.7-dev \
        python3-pip

WORKDIR ..

# Switch the system to use python3.7 by default - 2 is better than 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 2

RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools

# Simple default command to dump GPU related details.  This will only work with a docker driver of nvidia-docker
#CMD ["sh","-c","nvidia-smi"]

