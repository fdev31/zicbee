#!/bin/sh

ENV_NAME="zicbee_hive"
if [ $# -eq 1 ]; then
    SRC=$1
else
    SRC=
fi

die () {
    echo "DIED on $1."
    exit
}

for pyversion in 2.5 2.6; do
    unset VIRTUAL_ENV
    env_path=$ENV_NAME-py$pyversion
    if [ -d "./$env_path/" ]; then
        echo "Using existing directory."
    else
        rm -fr env_path
        virtualenv --no-site-package -p python$pyversion $env_path || die
    fi

    cd $env_path || die "cd $env_path"
    . ./bin/activate # source the environment
    if [ $SRC ]; then
        URLS="$SRC/zicbee-mplayer $SRC/zicbee $SRC/zicbee-wasp"
    else
        URLS="http://zicbee.gnux.info/hg/index.cgi/zicbee-mplayer/archive/tip.zip http://zicbee.gnux.info/hg/index.cgi/zicbee/archive/tip.zip http://zicbee.gnux.info/hg/index.cgi/zicbee-wasp/archive/tip.zip"
    fi
    for url in $URLS; do
        ./bin/easy_install "$url" || die "install $url"
    done
    VERSION=`./bin/python -c "import zicbee; print zicbee.__version__"`
    cd ..
    virtualenv --no-site-packages --relocatable -p python$pyversion $env_path || die "relocating"
    tar cvfh - $env_path | bzip2 -9 > ${ENV_NAME}-${VERSION}-py${pyversion}.tbz
done

