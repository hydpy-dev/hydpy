#!python3

import sys
import textwrap

logfilename = 'HydPy2FEWS.log'
with open(logfilename, 'w'):
    pass

try:
    from hydpy.auxs.xmltools import execute_workflow
    execute_workflow(argv=sys.argv)
except BaseException as exc:
    with open(logfilename, 'a') as file_:
        arguments = ', '.join(sys.argv)
        message = '\n'.join(textwrap.wrap(str(exc)))
        file_.write(
            f'Executing the workflow script with arguments `{arguments}` '
            f'resulted in the following error:\n{message}\n')
