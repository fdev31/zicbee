#!/bin/sh

CLEAN=true

die () {
    echo "DIED on $1."
    exit 1
}

dn=`dirname $0`
if [ $dn = '.' ]; then
    env_path=$PWD
else
    env_path=$dn
fi
env_path=`dirname $env_path`

cd $env_path || die "cd $env_path"
. ./bin/activate # source the environment

if [ $# -eq 1 ]; then
    SRC=$1
else
    SRC=
fi

rm -fr usr/lib/python*/site-package/zicbee*

if [ $SRC ]; then
    URLS="$SRC/zicbee-lib $SRC/zicbee $SRC/zicbee-mplayer $SRC/zicbee-vlc"
else
    URLS="http://zicbee.gnux.info/hg/index.cgi/zicbee-lib/archive/tip.zip http://zicbee.gnux.info/hg/index.cgi/zicbee-mplayer/archive/tip.zip http://zicbee.gnux.info/hg/index.cgi/zicbee/archive/tip.zip http://zicbee.gnux.info/hg/index.cgi/zicbee-vlc/archive/tip.zip"
fi

for url in $URLS; do
    ./bin/easy_install -U "$url" || die "install $url"
done

wasp help || die "Can't run wasp!"
zicdb help || die "Can't run zicdb!"
zicserve || die "Can't run zicserve!"
wasp kill

