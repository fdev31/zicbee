#!/bin/sh

# SOME VARIABLES

OUT=zicbee
FMT=png
TMP=${OUT}.dot
CACHE=${OUT}.importcache

# ENSURE THE PNG IS IN THE RIGHT DIRECTORY

if [ `basename $PWD` = 'utils' ]
then
    OUT="utils/${OUT}"
    PREFIX="../"
    cd $PREFIX
fi

# UTILITY FUNCTION

install () {
    # EXITS with a nice message about the missing program
    # (argument is program name)
    what=$1
    if [ ${what} = "dot" ]
    then
        echo "Please install graphviz (dot executable is not accessible)"
    else
        echo "Please install ${what} (try easy_install ${what})"
    fi
    exit 255
}

# HERE BEGINS

if [ ! -f ${CACHE} ]; then
    echo "Generating cache..."
    findimports --write-cache ${CACHE} zicbee || install findimports
else
    echo "Using cached data (remove ${PREFIX}${CACHE} if needed)"
fi

echo "Generating graph..."
findimports ${CACHE} -d > ${TMP} || install findimports

echo "Rendering..."
dot -T${FMT} -o"${PREFIX}${OUT}.${FMT}" ${TMP} || install dot

