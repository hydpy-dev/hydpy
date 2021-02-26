import os
import warnings

if os.environ.get("COVERAGE_PROCESS_START") is not None:
    import coverage

    try:
        coverage.process_startup()
    except coverage.misc.CoverageException as exc:
        warnings.warn(
            f"Something wrong with how HydPy measures code "
            f"coverage during testing: {exc}")
