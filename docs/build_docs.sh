#!/usr/bin/env bash
echo Building docs

# This is a very minimal file for sphinx generation.  It assumes Sphinx is pip installed, geneates html


SPHINXBUILD=sphinx-build
SOURCEDIR=$CTX_HOME/rightsize/docs/source
BUILDDIR=$CTX_HOME/rightsize/docs/build
#SPHINXOPTS="-c ."

echo "ctx home is $CTX_HOME"
echo "source directory is $SOURCEDIR"
echo "build directory is $BUILDDIR"

sphinx-apidoc -o $SOURCEDIR $CTX_HOME/rightsize/rightsize
$SPHINXBUILD -M html $SOURCEDIR $BUILDDIR $SPHINXOPTS