
import os
import webbrowser

os.system(r'make clean')
os.system(r'make html')
#os.system(r'make pdf')

paths = [os.path.join('_build', 'html', fn)
         for fn in os.listdir(os.path.join('_build', 'html'))
         if fn.endswith('.html')]
for path in paths:
    lines = []
    for line in open(path):
        if line.startswith('<dd><p>alias of <a class="reference external"'):
            line = line.split('span')[1]
            line = line.split('>')[1]
            line = line.split('<')[0]
            lines[-1] = lines[-1].replace(
                    'TYPE</code>',
                    'TYPE</code><em class="property"> = %s</em>' % line)
        else:
            lines.append(line)
    open(path, 'w').write(''.join(lines))


os.chdir(r'C:\Program Files (x86)\Mozilla Firefox')
webbrowser.register('firefox', None, webbrowser.GenericBrowser('firefox'), 1)
webbrowser.get('firefox').open_new_tab(
                                r'C:\HydPy\hydpy\docs\_build\html\index.html')
