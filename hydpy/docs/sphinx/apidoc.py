# -*- coding: utf-8 -*-
"""Generate and polish the HTML documentation."""
import os

os.system(r"make clean")
os.system(r"make html")

folder = "../_built/html"
filenames = sorted(fn for fn in os.listdir(folder) if fn.endswith(".html"))
for path in (os.path.join(folder, fn) for fn in filenames):
    lines: list[str] = []
    with open(path, encoding="utf-8") as file_:
        for line in file_.readlines():
            if line.startswith('<dd><p>alias of <a class="reference external"'):
                line = line.split("span")[1]
                line = line.split(">")[1]
                line = line.split("<")[0]
                lines[-1] = lines[-1].replace(
                    "TYPE</code>", f'TYPE</code><em class="property"> = {line}</em>'
                )
            else:
                lines.append(line)
    with open(path, "w", encoding="utf-8") as file_:
        file_.write("".join(lines))
