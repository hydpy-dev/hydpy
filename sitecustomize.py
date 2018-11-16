import coverage
import os
cps = os.environ.get('COVERAGE_PROCESS_START')
if cps is None:
    print('\nStarting Python process without coverage measurement.\n')
else:
    print(f'\nStarting Python process with coverage measurement based '
          f'on configuration file `{cps}`.  Look for the result file '
          f'in directory `{os.path.abspath(".")}`.\n')
coverage.process_startup()
