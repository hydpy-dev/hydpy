import os
if os.environ.get('COVERAGE_PROCESS_START') is not None:
    import coverage
    coverage.process_startup()
