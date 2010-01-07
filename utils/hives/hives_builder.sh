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


echo -n "Start from scratch ? [y/N] "
read yn

if [ $yn = "n" ]; then
    clean=
else
    clean='yes'
    echo "Starting from scratch!"
fi

for pyversion in $PY_VERSIONS; do
    unset VIRTUAL_ENV
    env_path=$ENV_NAME-py$pyversion
    if [ $clean ]; then
        rm -fr $env_path
    fi
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

    echo "Fixing executables..."
    for prog in zicdb zicserve wasp; do
        rm -f $prog
        sed 's/dirname(__file__),/dirname(__file__), "bin",/' < bin/$prog > $prog
        chmod +x $prog
    done
    for prog in python easy_install; do
        rm -f bin/$prog
        suffix="-$pyversion"
        if [ $prog = "python" ]; then
            suffix="$pyversion"
        fi
        echo "ln -s ${prog}${suffix} bin/$prog"
        ln -s "./${prog}${suffix}" "bin/$prog"
    done

    VERSION=`./bin/python -c "import zicbee; print zicbee.__version__"`
    cd ..
    echo "Relocating..."
    virtualenv --no-site-packages --relocatable -p python$pyversion $env_path || die "relocating"
    echo "Clean up..."
    find $env_path -name "*.py[oc]" -exec rm {} \;
    echo "Packaging..."
    tar cfh - $env_path | bzip2 -9 > ${ENV_NAME}-${VERSION}-py${pyversion}.tbz
    echo "Done."
done

