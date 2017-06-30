# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 12:44:08 2017

@author: tyralla
"""
from __future__ import division, print_function
import os
import sys

try:
    folder = os.path.join('target', 'doc', 'build')
    paths = [os.path.join(folder, fn) for fn in os.listdir(folder)
             if fn.endswith('.html')]
    for path in paths:
        lines = []
        with open(path) as file_:
            for line in file_:
                if line.startswith('<dd><p>alias of <a '
                                   'class="reference external"'):
                    line = line.split('span')[1]
                    line = line.split('>')[1]
                    line = line.split('<')[0]
                    lines[-1] = lines[-1].replace(
                           'TYPE</code>',
                           'TYPE</code><em class="property"> = %s</em>' % line)
                else:
                    lines.append(line)
        with open(path, 'w') as file_:
            file_.write(''.join(lines))
except BaseException as exc:
    print(exc)
    sys.exit(1)
else:
    sys.exit(0)
