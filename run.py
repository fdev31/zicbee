#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys

for name in os.listdir('eggs'):
    egg_name = os.path.join(os.curdir, 'eggs', name)
    if name.endswith('.egg') or os.path.isdir(egg_name):
        print "appending %s to your python path..."%name
        sys.path.append(egg_name)

from zicbee.core import startup
startup()
