# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 16:38:23 2017

@author: tyralla
"""

import numpy
from matplotlib import pyplot

from hydpy.core import objecttools


class Shape(object):

    last_instance = None

    def __init__(self, vertices, layer=None):
        self._setvertices(vertices)
        self.layer = self.DEFAULT_LAYER if layer is None else layer
        Shape.last_instance = self

    def norm(self, xmin, ymin, xmax, ymax):
        """Norm the original vertices defining the shape with the given
        boundary values."""
        self.vertices_norm = self.vertices_orig.copy()
        self.vertices_norm[:, 0] = (self.vertices_norm[:, 0]-xmin)/(xmax-xmin)
        self.vertices_norm[:, 1] = (ymax-self.vertices_norm[:, 1])/(ymax-ymin)

    def __repr__(self):
        prefix = '%s(' % objecttools.classname(self)
        blanks = ' '*len(prefix)
        lines = ['%slayer=%d,' % (prefix, self.layer)]
        subprefix = '%svertices=' % blanks
        if self.NDIM == 0:
            string = '%s%s' % (subprefix,
                               objecttools.repr_tuple(self.vertices_orig[0]))
        else:
            string = objecttools.assignrepr_tuple2(self.vertices_orig,
                                                   subprefix)
        lines.append(string + ')')
        return '\n'.join(lines)

    @property
    def xs_orig(self):
        return self.vertices_orig[:, 0]

    @property
    def ys_orig(self):
        return self.vertices_orig[:, 1]


class Point(Shape):
    """

    >>> from hydpy.gui.shapetools import Point
    >>> Point((1, 2))
    Point(layer=1,
          vertices=(1.0, 2.0))
    >>> point.Point(layer=2,
    ...             vertices=(3.0, 4.0))
    >>> point
    Point(layer=2,
          vertices=(3.0, 4.0))
    >>> point.plot()
    """
    NDIM = 0
    DEFAULT_LAYER = 3

    def _setvertices(self, vertices):
        self.vertices_orig = numpy.full((1, 2), vertices, dtype=float)

    def plot(self, **kwargs):
        if 'marker' not in kwargs:
            kwargs['marker'] = 'o'
        pyplot.plot(self.xs_orig, self.ys_orig, **kwargs)


class Multi(Shape):

    def _setvertices(self, vertices):
        self.vertices_orig = numpy.full((len(vertices), 2),
                                        vertices, dtype=float)


class Line(Multi):
    """

    >>> from hydpy.gui.shapetools import Line
    >>> Line(((1, 2), (3, 4)))
    Line(layer=1,
         vertices=((1.0, 2.0),
                   (3.0, 4.0)))
    >>> line = Line(layer=2,
    ...             vertices=((1.0, 2.0),
    ...                       (3.0, 1.0),
    ...                       (5.0, 1.5)))
    >>> line
    Line(layer=2,
         vertices=((1.0, 2.0),
                   (3.0, 1.0),
                   (5.0, 1.5)))
    >>> line.plot()

    """
    NDIM = 1
    DEFAULT_LAYER = 2

    def plot(self, **kwargs):
        pyplot.plot(self.xs_orig, self.ys_orig, **kwargs)


class Plane(Multi):
    """

    >>> from hydpy.gui.shapetools import Plane
    >>> Plane(((1, 2), (3, 4), (5, 6)))
    Plane(layer=1,
          vertices=((1.0, 1.0),
                    (3.0, 4.0),
                    (5.0, 6.0)))
    >>> plane = Plane(layer=2,
    ...               vertices=((1.0, 1.0),
    ...                         (3.0, 2.0),
    ...                         (2.5, 3.0)))
    >>> plane
    Plane(layer=2,
          vertices=((1.0, 1.0),
                    (3.0, 2.0),
                    (2.5, 3.0)))
    >>> plane.plot()
    """
    NDIM = 2
    DEFAULT_LAYER = 1

    def plot(self, **kwargs):
        xs = list(self.xs_orig) + [self.xs_orig[0]]
        ys = list(self.ys_orig) + [self.ys_orig[0]]
        pyplot.plot(xs, ys, **kwargs)
