# -*- coding: utf-8 -*-
"""This module implements tools for file related string substitutions."""

# import...
# ...from standard library

# ...from HydPy
from hydpy.core import objecttools


def xml_replace(filename, **replacements):
    """Read the content of an XML template file (XMLT), apply the given
    `replacements` ot its substitution  markers, and write the result into
    an XML file with the same name but ending with `xml` instead of `xmlt`.

    First, we write an XMLT file, containing a regular HTML comment, a
    readily defined element `e1`, and some other elements with
    substitutions markers.  Substitution markers are HTML comments
    starting and ending with the `|` character:

    >>> from hydpy import xml_replace, TestIO
    >>> with TestIO():
    ...     with open('test.xmlt', 'w') as templatefile:
    ...         _ = templatefile.write(
    ...             '<!--a normal comment-->\\n'
    ...             '<e1>element 1</e1>\\n'
    ...             '<e2><!--|e2|--></e2>\\n'
    ...             '<e3><!--|e3_|--></e3>\\n'
    ...             '<e4><!--|e4=element 4|--></e4>\\n'
    ...             '<e2><!--|e2|--></e2>')

    Each substitution marker must be met by a keyword argument unless
    it holds a default value (`e4`).  All arguments are converted to
    a |str| object (`e3`).  Template files can use the same substitution
    marker multiple times (`e2`):

    >>> with TestIO():
    ...     xml_replace('test', e2='E2', e3_=3)
    ...     with open('test.xml') as targetfile:
    ...         print(targetfile.read())
    <!--a normal comment-->
    <e1>element 1</e1>
    <e2>E2</e2>
    <e3>3</e3>
    <e4>element 4</e4>
    <e2>E2</e2>
    >>> with TestIO():
    ...     xml_replace('test', e2='E2', e3_=3, e4='ELEMENT 4')
    ...     with open('test.xml') as targetfile:
    ...         print(targetfile.read())
    <!--a normal comment-->
    <e1>element 1</e1>
    <e2>E2</e2>
    <e3>3</e3>
    <e4>ELEMENT 4</e4>
    <e2>E2</e2>

    Missing and useless keyword arguments result in errors:

    >>> with TestIO():
    ...     xml_replace('test', e2='E2')
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to replace the markers `e2, e3_, and e4` \
of the XML template file `test.xmlt` with the available keywords `e2`, \
the following error occurred: Marker `e3_` cannot be replaced.

    >>> with TestIO():
    ...     xml_replace('test', e2='e2', e3_='E3', e4='e4', e5='e5')
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to replace the markers `e2, e3_, and e4` \
of the XML template file `test.xmlt` with the available keywords `e2, e3_, \
e4, and e5`, the following error occurred: Keyword(s) `e5` cannot be used.

    Using different default values for the same substitution marker
    is not allowed:

    >>> from hydpy import xml_replace, TestIO
    >>> with TestIO():
    ...     with open('test.xmlt', 'w') as templatefile:
    ...         _ = templatefile.write(
    ...             '<e4><!--|e4=element 4|--></e4>\\n'
    ...             '<e4><!--|e4=ELEMENT 4|--></e4>')

    >>> with TestIO():
    ...     xml_replace('test', e4=4)
    ...     with open('test.xml') as targetfile:
    ...         print(targetfile.read())
    <e4>4</e4>
    <e4>4</e4>

    >>> with TestIO():
    ...     xml_replace('test')
    Traceback (most recent call last):
    ...
    RuntimeError: Template file `test.xmlt` defines different default values \
for marker `e4`.
    """
    keywords = set(replacements.keys())
    templatename = f'{filename}.xmlt'
    targetname = f'{filename}.xml'
    with open(templatename) as templatefile:
        templatebody = templatefile.read()
    parts = templatebody.replace('<!--|', '|-->').split('|-->')
    defaults = {}
    for idx, part in enumerate(parts):
        if idx % 2:
            subparts = part.partition('=')
            if subparts[2]:
                parts[idx] = subparts[0]
                if subparts[0] not in replacements:
                    if ((subparts[0] in defaults) and
                            (defaults[subparts[0]] != str(subparts[2]))):
                        raise RuntimeError(
                            f'Template file `{templatename}` defines different '
                            f'default values for marker `{subparts[0]}`.')
                    defaults[subparts[0]] = str(subparts[2])
    markers = parts[1::2]
    try:
        unused_keywords = keywords.copy()
        for idx, part in enumerate(parts):
            if idx % 2:
                newpart = replacements.get(part, defaults.get(part))
                if newpart is None:
                    raise RuntimeError(
                        f'Marker `{part}` cannot be replaced.')
                parts[idx] = str(newpart)
                unused_keywords.discard(part)
        targetbody = ''.join(parts)
        if unused_keywords:
            raise RuntimeError(
                f'Keyword(s) `{objecttools.enumeration(unused_keywords)}` '
                f'cannot be used.')
        with open(targetname, 'w') as targetfile:
            targetfile.write(targetbody)
    except BaseException:
        objecttools.augment_excmessage(
            f'While trying to replace the markers '
            f'`{objecttools.enumeration(sorted(set(markers)))}` of the '
            f'XML template file `{templatename}` with the available '
            f'keywords `{objecttools.enumeration(sorted(keywords))}`')
