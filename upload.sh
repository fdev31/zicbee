#!/bin/sh
python setup.py sdist --formats=gztar,zip,bztar upload
for py_ver in 2.5 2.5
do
    python${py_ver} setup.py bdist_egg upload
done
