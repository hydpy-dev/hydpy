"""Better remove the "USEAUTODOC" option soon..."""

with open("hydpy/config.py", encoding="utf-8") as configfile:
    text = configfile.read()
text = text.replace("USEAUTODOC = False", "USEAUTODOC = True")
with open("hydpy/config.py", "w", encoding="utf-8") as configfile:
    configfile.write(text)
