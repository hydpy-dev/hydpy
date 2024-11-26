"""Combine the currently generated documentation with the existing ones of the
`available_doc_versions` branch and update this branch (which delete its history
entirely).

This script works on Travis-CI.  To use it somewhere else, set the environment variable
`TRAVIS_BRANCH` to the current branch name.  But we aware of the "git config..."
command below.  I do not know if it modifies  your git configuration permanently.

This script does not push anything to Github-Pages.
"""

import os
import shutil
import sys


def print_(*message: str) -> None:
    """Print immediately."""
    print(*message)
    sys.stdout.flush()


def call(command: str) -> None:
    """`os.system` with direct termination in the event of an error."""
    code = os.system(command)
    if code:
        sys.exit(1)


shutil.copy("hydpy/docs/publish_docs.py", "publish_docs_copy.py")

print_('Check out the "available_doc_versions" branch:')
call("git config --replace-all remote.origin.fetch +refs/heads/*:refs/remotes/origin/*")
call("git fetch --all")
call("git checkout --track origin/available_doc_versions")

branch2version: dict[str, str] = {}
with open("relevant_branches.txt", encoding="utf-8") as file_:
    for line in file_.readlines()[1:]:
        try:
            branch, version = line.split()
        except TypeError:
            continue
        else:
            branch2version[branch] = version

print_("Relevant branch/version names:")
for branch, version in branch2version.items():
    print_("\t", branch, version)

actual_branch = os.environ["TRAVIS_BRANCH"]
print_("Actual branch name:")
print_(f"\t{actual_branch}")
if actual_branch not in branch2version:
    sys.exit(0)

actual_version = branch2version[actual_branch]
if os.path.exists(actual_version):
    print_("Remove the old documentation of branch", actual_branch)
    shutil.rmtree(actual_version)
print_("Activate the new documentation of branch", actual_branch)
for dirpath, _, _ in os.walk(os.path.join(".nox", "sphinx")):
    if os.path.split(dirpath)[-1] == "site-packages":
        buildpath = os.path.join(dirpath, "hydpy", "docs", "auto", "build")
        if os.path.exists(buildpath):
            break
else:
    raise RuntimeError("Cannot find Sphinx's build path.")
shutil.move(buildpath, actual_version)

print_("Update and squash the remote `available_doc_versions` branch:")
call(f"git add {actual_version}")
call(f'git commit -m "update branch {actual_branch}"')
call("git checkout 57c347f3c01818777aeea4e71c4f5bb884e48216 -b temp")
call("git merge --squash available_doc_versions")
call('git commit -m "update docs"')

if (token := os.environ.get("GH_TOKEN")) is None:
    print_("Not authorised to push to branch `available_doc_versions`")
else:
    repo = os.environ["TRAVIS_REPO_SLUG"]
    remote = f"https://{token}@github.com/{repo}.git"
    call(f"git push {remote} temp:available_doc_versions -f")

print_("Move everything relevant to the final results folder:")
os.makedirs("result")
shutil.copy(".gitignore", "result/.gitignore")
shutil.copy("relevant_branches.txt", "result/relevant_branches.txt")
shutil.copy("index.html", "result/index.html")
for version in branch2version.values():
    target = os.path.join("result", version)
    print_(f"\t{version} --> {target}")
    shutil.move(version, target)

print_("Search for the relevant HTML files:")
version2htmls: dict[str, tuple[str, ...]] = {}
for version in branch2version.values():
    print_(f"\tversion {version}")
    folderpath = os.path.join("result", version)
    version2htmls[version] = tuple(
        filename for filename in os.listdir(folderpath) if filename.endswith(".html")
    )

print_("Update all relevant HTML files:")
for version1, htmls1 in version2htmls.items():
    print_(f"\tUpdate version {version1}")
    for html1 in htmls1:
        filepath1 = os.path.join("result", version1, html1)
        with open(filepath1, encoding="utf-8-sig") as file_:
            text = file_.read()
        try:
            idx = text.index('<div id="searchbox"')
        except ValueError:
            continue
        if idx <= 0:
            continue
        links: list[str] = []
        for version2, htmls2 in version2htmls.items():
            if html1 in htmls2:
                links.append(f'<li><a href="../{version2}/{html1}">{version2}</a></li>')
        if not links:
            continue
        print_(f"\t\tUpdate file {html1}")
        above = text[:idx]
        below = text[idx:]
        jdx = above.rfind("</div>")
        below = f"{above[jdx:]}{below}"
        above = above[:jdx]
        text = "\n".join(
            (above, "<h3>Versions</h3>", "<ul>", "\n".join(links), "</ul>", below)
        )
        with open(filepath1, "w", encoding="utf-8-sig") as file_:
            file_.write(text)
