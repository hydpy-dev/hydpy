
import os
import webbrowser

os.system(r'make clean')
os.system(r'make html')

folder = r'C:\HydPy\hydpy\docs\auto\_build\html'
paths = [os.path.join(folder, fn) for fn in os.listdir(folder)
         if fn.endswith('.html')]
for path in paths:
        lines = []
        with open(path) as file_:
            for line in file_:
                if line.startswith('<dd><p>alias of <a '
                                   'class="reference external"'):
                    line = line.split('span')[1]
                    line = line.split('>')[1]
                    line = line.split('<')[0]
                    lines[-1] = lines[-1].replace(
                           'TYPE</code>',
                           'TYPE</code><em class="property"> = %s</em>' % line)
                else:
                    lines.append(line)
        with open(path, 'w') as file_:
            file_.write(''.join(lines))

os.chdir(r'C:\Program Files (x86)\Mozilla Firefox')
webbrowser.register('firefox', None, webbrowser.GenericBrowser('firefox'), 1)
webbrowser.get('firefox').open_new_tab(os.path.join(folder, 'index.html'))
