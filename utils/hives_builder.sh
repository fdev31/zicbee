#!/bin/sh

ENV_NAME="zicbee_hive"
if [ $# -gt 1 ]; then
    SRC=$1
else
    SRC=~/dev
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
    ./bin/easy_install $SRC/zicbee-mplayer || die "install zicbee-mplayer"
    ./bin/easy_install $SRC/zicbee || die "install zicbee"
    ./bin/easy_install $SRC/zicbee-wasp || die "install zicbee"
    VERSION=`./bin/python -c "import zicbee; print zicbee.__version__"`
    cd ..
    virtualenv --relocatable -p python$pyversion $env_path || die "relocating"
    tar cvfh - $env_path | bzip2 -9 > ${ENV_NAME}-${VERSION}-py${pyversion}.tbz
done

