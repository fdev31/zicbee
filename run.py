#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys

for path in ('%s%seggs/%s'%(os.curdir, os.path.sep, egg) for egg in os.listdir('eggs') if egg.endswith('.egg') or os.path.isdir(egg)):
    sys.path.appendpath)

from zicbee.core import startup
startup()
