"""Push the `result` folder prepared by the `combine_docversions.py` script to
Github-Pages.

Only pushes when the current branch is among the relevant branches listed in
`relevant_branches.txt`.
"""

import os
import sys

import ghp_import


def print_(*message: str) -> None:
    """Print immediately."""
    print(*message)
    sys.stdout.flush()


def main() -> None:
    """Push when appropriate."""

    if (token := os.environ.get("GH_TOKEN")) is not None:
        repo = os.environ["TRAVIS_REPO_SLUG"]
        remote = f"https://{token}@github.com/{repo}.git"
        actual_branch = os.environ["TRAVIS_BRANCH"]

        with open("relevant_branches.txt", encoding="utf-8") as file_:
            lines = file_.readlines()[1:]

        for line in lines:
            try:
                branch = line.split()[0]
            except IndexError:
                continue
            if branch == actual_branch:
                print_("Push to GitHub-Pages:")
                ghp_import.ghp_import(
                    srcdir="result",
                    remote=remote,
                    branch="gh-pages",
                    mesg="update documentation",
                    push=True,
                    prefix=None,
                    force=True,
                    nojekyll=True,
                )
                break

    print_("No push to GitHub-Pages.")


main()
