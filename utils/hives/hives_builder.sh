#!/bin/sh
cd `dirname $0`

ENV_NAME="zicbee_hive"
PY_VERSIONS="2.5 2.6"

if [ $# -eq 1 ]; then
    SRC=$1
elif [ $# -eq 2 ]; then
    SRC=$1
    shift
    PY_VERSIONS=$*
else
    SRC=
fi

die () {
    echo "DIED on $1."
    exit 1
}

for pyversion in $PY_VERSIONS; do
    unset VIRTUAL_ENV
    env_path=$ENV_NAME-py$pyversion
    echo "Getting Python $pyversion environment..."
    if [ -d "./$env_path/" ]; then
        echo "Using existing directory."
    else
        rm -fr env_path
        virtualenv --no-site-package -p python$pyversion $env_path || die
    fi

    cd $env_path || die "cd $env_path"
    cp ../hive_upgrade_script.sh ./UPGRADE
    ./UPGRADE $SRC || die "upgrade failed"
    for prog in zicdb zicserve wasp; do
        rm $prog
        sed 's/dirname(__file__),/dirname(__file__), "bin",/' < bin/$prog > $prog
        chmod +x $prog
    done
    for prog in python easy_install; do
        rm -f bin/$prog
        if [ prog != "python" ]; then
            ln -s bin/$prog-$pyversion $prog
        else
            ln -s bin/$prog$pyversion $prog
        fi
    done

    VERSION=`./bin/python -c "import zicbee; print zicbee.__version__"`
    cd ..
    virtualenv --no-site-packages --relocatable -p python$pyversion $env_path || die "relocating"
    find $env_path -name "*.py[oc]" -exec rm {} \;
    tar cvfh - $env_path | bzip2 -9 > ${ENV_NAME}-${VERSION}-py${pyversion}.tbz
done

