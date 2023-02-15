# -*- coding: utf-8 -*-
"""This module implements tools for file related string substitutions."""

# import...
# ...from HydPy
from hydpy import config
from hydpy.core import objecttools
from hydpy.core.typingtools import *


def xml_replace(filename: str, *, printflag: bool = True, **replacements: str) -> None:
    """Read the content of an XML template file (XMLT), apply the given
    `replacements` to its substitution  markers, and write the result into
    an XML file with the same name but ending with `xml` instead of `xmlt`.

    First, we write an XMLT file, containing a regular HTML comment, a
    readily defined element `e1`, and some other elements with
    substitutions markers.  Substitution markers are HTML comments
    starting and ending with the `|` character:

    >>> from hydpy import xml_replace, TestIO
    >>> with TestIO():
    ...     with open("test1.xmlt", "w") as templatefile:
    ...         _ = templatefile.write(
    ...             "<!--a normal comment-->\\n"
    ...             "<e1>element 1</e1>\\n"
    ...             "<e2><!--|e2|--></e2>\\n"
    ...             "<e3><!--|e3_|--></e3>\\n"
    ...             "<e4><!--|e4=element 4|--></e4>\\n"
    ...             "<e2><!--|e2|--></e2>")

    Function |xml_replace| can both be called within a Python session and
    from a command line.  We start with the first type of application.

    Each substitution marker must be met by a keyword argument unless
    it holds a default value (`e4`).  All arguments are converted to
    a |str| object (`e3`).  Template files can use the same substitution
    marker multiple times (`e2`):

    >>> with TestIO():
    ...     xml_replace("test1", e2="E2", e3_=3, e4="ELEMENT 4")
    template file: test1.xmlt
    target file: test1.xml
    replacements:
      e2 --> E2 (given argument)
      e3_ --> 3 (given argument)
      e4 --> ELEMENT 4 (given argument)
      e2 --> E2 (given argument)
    >>> with TestIO():
    ...     with open("test1.xml") as targetfile:
    ...         print(targetfile.read())
    <!--a normal comment-->
    <e1>element 1</e1>
    <e2>E2</e2>
    <e3>3</e3>
    <e4>ELEMENT 4</e4>
    <e2>E2</e2>

    Without custom values, |xml_replace| applies predefined default
    values, if available (`e4`):

    >>> with TestIO():
    ...     xml_replace("test1", e2="E2", e3_=3)    # doctest: +ELLIPSIS
    template file: test1.xmlt
    target file: test1.xml
    replacements:
      e2 --> E2 (given argument)
      e3_ --> 3 (given argument)
      e4 --> element 4 (default argument)
      e2 --> E2 (given argument)
    >>> with TestIO():
    ...     with open("test1.xml") as targetfile:
    ...         print(targetfile.read())
    <!--a normal comment-->
    <e1>element 1</e1>
    <e2>E2</e2>
    <e3>3</e3>
    <e4>element 4</e4>
    <e2>E2</e2>

    Missing and useless keyword arguments result in errors:

    >>> with TestIO():
    ...     xml_replace("test1", e2="E2")
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to replace the markers `e2, e3_, and e4` \
of the XML template file `test1.xmlt` with the available keywords `e2`, \
the following error occurred: Marker `e3_` cannot be replaced.

    >>> with TestIO():
    ...     xml_replace("test1", e2="e2", e3_="E3", e4="e4", e5="e5")
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to replace the markers `e2, e3_, and e4` \
of the XML template file `test1.xmlt` with the available keywords `e2, e3_, \
e4, and e5`, the following error occurred: Keyword(s) `e5` cannot be used.

    Using different default values for the same substitution marker
    is not allowed:

    >>> from hydpy import pub, TestIO, xml_replace
    >>> with TestIO():
    ...     with open("test2.xmlt", "w") as templatefile:
    ...         _ = templatefile.write(
    ...             "<e4><!--|e4=element 4|--></e4>\\n"
    ...             "<e4><!--|e4=ELEMENT 4|--></e4>")

    >>> with TestIO():
    ...     xml_replace("test2", e4=4)
    template file: test2.xmlt
    target file: test2.xml
    replacements:
      e4 --> 4 (given argument)
      e4 --> 4 (given argument)

    >>> with TestIO():
    ...     with open("test2.xml") as targetfile:
    ...         print(targetfile.read())
    <e4>4</e4>
    <e4>4</e4>

    >>> with TestIO():
    ...     xml_replace("test2")
    Traceback (most recent call last):
    ...
    RuntimeError: Template file `test2.xmlt` defines different default values \
for marker `e4`.

    As mentioned above, function |xml_replace| is registered as a "script
    function" and can thus be used via command line:

    >>> pub.scriptfunctions["xml_replace"].__name__
    'xml_replace'
    >>> pub.scriptfunctions["xml_replace"].__module__
    'hydpy.exe.replacetools'

    Use script |hyd| to execute function |xml_replace|:

    >>> from hydpy import run_subprocess
    >>> with TestIO():
    ...     result = run_subprocess(
    ...         'hyd.py xml_replace test1 e2="Element 2" e3_=3')
    template file: test1.xmlt
    target file: test1.xml
    replacements:
      e2 --> Element 2 (given argument)
      e3_ --> 3 (given argument)
      e4 --> element 4 (default argument)
      e2 --> Element 2 (given argument)

    >>> with TestIO():
    ...     with open("test1.xml") as targetfile:
    ...         print(targetfile.read())
    <!--a normal comment-->
    <e1>element 1</e1>
    <e2>Element 2</e2>
    <e3>3</e3>
    <e4>element 4</e4>
    <e2>Element 2</e2>
    """
    keywords = set(replacements.keys())
    templatename = f"{filename}.xmlt"
    targetname = f"{filename}.xml"
    if printflag:
        print(f"template file: {templatename}")
        print(f"target file: {targetname}")
        print("replacements:")
    with open(templatename, encoding=config.ENCODING) as templatefile:
        templatebody = templatefile.read()
    parts = templatebody.replace("<!--|", "|-->").split("|-->")
    defaults: Dict[str, str] = {}
    for idx, part in enumerate(parts):
        if idx % 2:
            subparts = part.partition("=")
            if subparts[2]:
                parts[idx] = subparts[0]
                if subparts[0] not in replacements:
                    if (subparts[0] in defaults) and (
                        defaults[subparts[0]] != str(subparts[2])
                    ):
                        raise RuntimeError(
                            f"Template file `{templatename}` defines different "
                            f"default values for marker `{subparts[0]}`."
                        )
                    defaults[subparts[0]] = str(subparts[2])
    markers = parts[1::2]
    try:
        unused_keywords = keywords.copy()
        for idx, part in enumerate(parts):
            if idx % 2:
                argument_info = "given argument"
                newpart = replacements.get(part)
                if newpart is None:
                    argument_info = "default argument"
                    newpart = defaults.get(part)
                if newpart is None:
                    raise RuntimeError(f"Marker `{part}` cannot be replaced.")
                if printflag:
                    print(f"  {part} --> {newpart} ({argument_info})")
                parts[idx] = str(newpart)
                unused_keywords.discard(part)
        targetbody = "".join(parts)
        if unused_keywords:
            raise RuntimeError(
                f"Keyword(s) `{objecttools.enumeration(unused_keywords)}` "
                f"cannot be used."
            )
        with open(targetname, "w", encoding=config.ENCODING) as targetfile:
            targetfile.write(targetbody)
    except BaseException:
        objecttools.augment_excmessage(
            f"While trying to replace the markers "
            f"`{objecttools.enumeration(sorted(set(markers)))}` of the "
            f"XML template file `{templatename}` with the available "
            f"keywords `{objecttools.enumeration(sorted(keywords))}`"
        )
