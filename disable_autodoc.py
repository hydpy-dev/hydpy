
with open('hydpy/config.py') as configfile:
    text = configfile.read()
text = text.replace('USEAUTODOC = True', 'USEAUTODOC = False')
with open('hydpy/config.py', 'w') as configfile:
    configfile.write(text)
