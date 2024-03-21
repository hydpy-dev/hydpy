"""Create sketches of the structure of the application models.

This script creates only the sketches of the first four H-Land application models.
I plan to add other application models gradually.  Before doing so, the script requires
some refactoring.

For now, calling this script is not part of our Travis-CI workflow.  So we have to run
the script and exchange the resulting png files manually each time something changes.
"""

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import os
from typing import Final, Literal, NamedTuple, Optional, Union

from matplotlib import pyplot
import numpy

TOL: Final = 0.2  # total outlet length
HOW: Final = 0.05  # half outlet width
GOL: Final = 0.618  # golden ratio
TDX: Final = 0.02  # dx for left or right aligned text


@dataclass
class CellExtent:
    x0: float
    x1: float
    y0: float
    y1: float

    @property
    def dx(self) -> float:
        return self.x1 - self.x0

    @property
    def dy(self) -> float:
        return self.y1 - self.y0


@dataclass
class Index:
    i0: int
    j0: int
    i1: Optional[int] = None
    j1: Optional[int] = None


@dataclass
class Grid:
    nrows: int
    ncols: int
    xs: tuple[float, ...] = field(init=False)
    ys: tuple[float, ...] = field(init=False)
    dx: float = field(init=False)
    dy: float = field(init=False)

    def __post_init__(self) -> None:
        self.xs = tuple(numpy.linspace(0.0, 1.0, self.ncols + 1))
        self.ys = tuple(numpy.linspace(0.0, 1.0, self.nrows + 1))
        self.dx = self.xs[1] - self.xs[0]
        self.dy = self.ys[1] - self.ys[0]

    def get_cellextent(self, index: Index) -> CellExtent:
        j1 = (index.j0 if index.j1 is None else index.j1) + 1
        i1 = (index.i0 if index.i1 is None else index.i1) + 1
        return CellExtent(
            x0=self.xs[index.j0], x1=self.xs[j1], y0=self.ys[index.i0], y1=self.ys[i1]
        )


@dataclass
class Margins:
    left: float = 0.1
    right: float = 0.1
    bottom: float = 0.0
    top: float = 0.0


class Point(NamedTuple):
    x: float
    y: float

    def adjust(self, cellextent: CellExtent, margins: Margins) -> Point:
        x0m = cellextent.x0 + margins.left * cellextent.dx
        x1m = cellextent.x1 - margins.right * cellextent.dx
        y0m = cellextent.y0 + margins.bottom * cellextent.dy
        y1m = cellextent.y1 - margins.top * cellextent.dy
        return type(self)(x=self.x * (x1m - x0m) + x0m, y=self.y * (y1m - y0m) + y0m)


class Points(list[Point]):
    def __init__(self, *args: Point) -> None:
        super().__init__(args)


@dataclass
class LineProperties:
    color: Literal["black", "grey", "white"] = "black"
    style: Literal["solid", "dashed", "dotted"] = "solid"
    width: float = 0.5


@dataclass
class TextProperties:
    color: Literal["black", "grey"] = "black"
    size: float = 9.0
    horizontal: Literal["left", "center", "right"] = "center"
    vertical: Literal["bottom", "center", "top"] = "bottom"


@dataclass
class ArrowProperties:
    color: Literal["black", "grey"] = "black"
    style: Literal["solid", "dashed", "dotted"] = "solid"
    linewidth: float = 0.25
    headwidth: float = 0.01


@dataclass
class Vectors:
    xs: Sequence[float]
    ys: Sequence[float]

    @classmethod
    def from_points(cls, points: Points) -> Vectors:
        return cls(
            xs=tuple(point[0] for point in points),
            ys=tuple(point[1] for point in points),
        )

    def adjust(self, cellextent: CellExtent, margins: Margins) -> Vectors:
        x0m = cellextent.x0 + margins.left * cellextent.dx
        x1m = cellextent.x1 - margins.right * cellextent.dx
        y0m = cellextent.y0 + margins.bottom * cellextent.dy
        y1m = cellextent.y1 - margins.top * cellextent.dy
        xs = numpy.array(self.xs, dtype=float)
        ys = numpy.array(self.ys, dtype=float)
        xs = xs * (x1m - x0m) + x0m
        ys = ys * (y1m - y0m) + y0m
        return type(self)(xs=tuple(xs), ys=tuple(ys))


@dataclass
class Element:
    index: Index
    margins: Optional[Margins] = None

    def plot(self, frame: Frame) -> None:
        raise NotImplementedError

    def draw_line(
        self,
        frame: Frame,
        points: Union[Points, Sequence[Points]],
        properties: LineProperties,
    ) -> None:
        if not isinstance(points, Points):
            points_ = points
        else:
            points_ = (points,)
        for points__ in points_:
            vectors = Vectors.from_points(points=points__)
            vectors = vectors.adjust(
                cellextent=frame.grid.get_cellextent(self.index),
                margins=frame.margins if self.margins is None else self.margins,
            )
            pyplot.plot(
                vectors.xs,
                vectors.ys,
                color=properties.color,
                linestyle=properties.style,
                linewidth=properties.width,
            )

    def _adjust_point(self, frame: Frame, point: Point) -> Point:
        return point.adjust(
            cellextent=frame.grid.get_cellextent(self.index),
            margins=frame.margins if self.margins is None else self.margins,
        )

    def draw_text(
        self, frame: Frame, text: str, point: Point, properties: TextProperties
    ) -> None:
        point = self._adjust_point(frame, point)
        pyplot.text(
            x=point.x,
            y=point.y,
            s=text,
            ha=properties.horizontal,
            va=properties.vertical,
            size=properties.size,
        )

    def draw_arrow(
        self, frame: Frame, base: Point, length: Point, properties: ArrowProperties
    ) -> None:
        base = self._adjust_point(frame=frame, point=base)
        pyplot.arrow(
            x=base.x,
            y=base.y,
            dx=length.x * frame.grid.dx,
            dy=length.y * frame.grid.dy,
            facecolor=properties.color,
            edgecolor=properties.color,
            linewidth=properties.linewidth,
            linestyle=properties.style,
            length_includes_head=True,
            head_width=properties.headwidth,
        )

    def draw_special_form(self, frame: Frame) -> None:
        top = 1.0
        self.draw_line(
            frame=frame,
            points=Points(
                Point(0.5 + HOW, 0.0),
                Point(0.5 + HOW, TOL),
                Point(1.0, TOL),
                Point(1.0, top),
                Point(0.0, top),
                Point(0.0, TOL),
                Point(0.5 - HOW, TOL),
                Point(0.5 - HOW, 0.0),
            ),
            properties=LineProperties(),
        )
        gol = GOL * (top - TOL) + TOL
        self.draw_line(
            frame=frame,
            points=Points(Point(0.0, gol), Point(top, gol)),
            properties=LineProperties(style="dotted"),
        )


@dataclass()
class Edge(Element):
    def plot(self, frame: Frame) -> None:
        self.draw_line(
            frame=frame,
            points=Points(
                Point(0.0, 0.0),
                Point(1.0, 0.0),
                Point(1.0, 1.0),
                Point(0.0, 1.0),
                Point(0.0, 0.0),
            ),
            properties=LineProperties(width=2.0, color="white"),
        )

    def __post_init__(self) -> None:
        self.margins = Margins(left=0.0, right=0.0)


@dataclass
class Title(Element):
    text: str = ""

    def plot(self, frame: Frame) -> None:
        self.draw_text(
            frame=frame,
            text=self.text,
            point=Point(0.5, 0.5),
            properties=TextProperties(vertical="center"),
        )


class Interception(Element):
    def plot(self, frame: Frame) -> None:
        self.draw_special_form(frame=frame)
        self.draw_text(
            frame=frame,
            text="ICMax",
            point=Point(TDX, 1.0),
            properties=TextProperties(horizontal="left"),
        )
        self.draw_text(
            frame=frame, text="IC", point=Point(0.5, TOL), properties=TextProperties()
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.7, 2.0),
            length=Point(0.0, -1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="P",
            point=Point(0.7 + TDX, 1.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.6, 1.0),
            length=Point(-0.2, 1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="EI",
            point=Point(0.5 + TDX, 1.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, 0.0),
            length=Point(0.0, -0.5),
            properties=ArrowProperties(headwidth=0.0),
        )
        self.draw_text(
            frame=frame,
            text="TF",
            point=Point(0.5 + TDX, -0.25),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, -0.5),
            length=Point(-0.1, -0.5),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="Snow",
            point=Point(0.4 - TDX, -0.75),
            properties=TextProperties(horizontal="right", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, -0.5),
            length=Point(0.1, -0.5),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="Rain",
            point=Point(0.6 + TDX, -0.75),
            properties=TextProperties(horizontal="left", vertical="center"),
        )


@dataclass
class Snow(Element):
    arrowfactor: float = 1.0
    include_sr: bool = False

    def plot(self, frame: Frame) -> None:
        self.draw_line(
            frame=frame,
            points=(
                Points(
                    Point(0.0, 1.0), Point(0.0, TOL), Point(0.5, TOL), Point(0.5, 1.0)
                ),
                Points(Point(0.5, TOL), Point(0.75 - HOW, TOL), Point(0.75 - HOW, 0.0)),
                Points(
                    Point(0.75 + HOW, 0.0),
                    Point(0.75 + HOW, TOL),
                    Point(1.0, TOL),
                    Point(1.0, 0.8),
                ),
                Points(Point(0.5, 0.8), Point(1.0, 0.8)),
            ),
            properties=LineProperties(),
        )
        self.draw_line(
            frame=frame,
            points=(
                Points(Point(0.0, 0.9), Point(0.5, 0.9)),
                Points(Point(0.5, 0.6), Point(1.0, 0.6)),
            ),
            properties=LineProperties(style="dotted"),
        )
        self.draw_text(
            frame=frame,
            text="SP⋅WHC",
            point=Point(0.99, 0.8),
            properties=TextProperties(horizontal="right"),
        )
        self.draw_text(
            frame=frame, text="SP", point=Point(0.25, TOL), properties=TextProperties()
        )
        self.draw_text(
            frame=frame, text="WC", point=Point(0.75, TOL), properties=TextProperties()
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.75, 0.0),
            length=Point(0.0, -1.0 * self.arrowfactor),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="In",
            point=Point(0.75 + TDX, -0.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        if self.include_sr:
            self.draw_text(
                frame=frame,
                text="SR",
                point=Point(0.63 - TDX, -0.5),
                properties=TextProperties(horizontal="left", vertical="center"),
            )
        self.draw_arrow(
            frame=frame,
            base=Point(0.4, 0.4),
            length=Point(0.2, 0.0),
            properties=ArrowProperties(linewidth=0.01),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.6, 0.4),
            length=Point(-0.2, 0.0),
            properties=ArrowProperties(linewidth=0.01),
        )


class Soil(Element):
    version: Literal["v1_v2", "v3_v4"] = "v1_v2"

    def plot(self, frame: Frame) -> None:
        top = 1.0
        if self.version == "v1_v2":
            self.draw_line(
                frame=frame,
                points=(
                    Points(
                        Point(0.25 - HOW, 0.0),
                        Point(0.25 - HOW, TOL),
                        Point(0.0, TOL),
                        Point(0.0, top),
                        Point(1.0, top),
                        Point(1.0, TOL),
                        Point(0.75 + HOW, TOL),
                        Point(0.75 + HOW, 0.0),
                    ),
                    Points(
                        Point(0.25 + HOW, 0.0),
                        Point(0.25 + HOW, TOL),
                        Point(0.75 - HOW, TOL),
                        Point(0.75 - HOW, 0.0),
                    ),
                ),
                properties=LineProperties(),
            )
            self.draw_line(
                frame=frame,
                points=Points(
                    Point(0.0, GOL * (top - TOL) + TOL),
                    Point(top, GOL * (top - TOL) + TOL),
                ),
                properties=LineProperties(color="grey"),
            )
        elif self.version == "v3_v4":
            self.draw_special_form(frame=frame)
        self.draw_text(
            frame=frame,
            text="FC",
            point=Point(TDX, 1.0),
            properties=TextProperties(horizontal="left"),
        )
        self.draw_text(
            frame=frame, text="SM", point=Point(0.5, TOL), properties=TextProperties()
        )
        if self.version == "v1_v2":
            x_r = 0.25
            self.draw_arrow(
                frame=frame,
                base=Point(0.75, -1.0),
                length=Point(0.0, 1.0),
                properties=ArrowProperties(),
            )
            self.draw_text(
                frame=frame,
                text="CF",
                point=Point(0.75 + TDX, -0.5),
                properties=TextProperties(horizontal="left", vertical="center"),
            )
        elif self.version == "v3_v4":
            x_r = 0.5
        else:
            raise NotImplementedError
        self.draw_arrow(
            frame=frame,
            base=Point(x_r, 0.0),
            length=Point(0.0, -1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="R",
            point=Point(x_r + TDX, -0.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.6, 1.0),
            length=Point(-0.2, 1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="EA",
            point=Point(0.5 + TDX, 1.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )


@dataclass
class Glacier(Element):
    def __post_init__(self) -> None:
        self.margins = Margins(right=0.5)

    def plot(self, frame: Frame) -> None:
        top = 0.7
        self.draw_line(
            frame=frame,
            points=(
                Points(
                    Point(0.5 + 2 * HOW, 0.0),
                    Point(0.5 + 2 * HOW, TOL),
                    Point(1.0, TOL),
                    Point(1.0, top),
                ),
                Points(
                    Point(0.0, top),
                    Point(0.0, TOL),
                    Point(0.5 - 2 * HOW, TOL),
                    Point(0.5 - 2 * HOW, 0.0),
                ),
            ),
            properties=LineProperties(),
        )
        self.draw_text(
            frame=frame,
            text="\u221E",
            point=Point(0.5, TOL),
            properties=TextProperties(),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, 0.0),
            length=Point(0.0, -1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="GLMelt",
            point=Point(0.5 + TDX, -0.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )


@dataclass
class UZ_SG1_BW(Element):
    arrows: bool = True

    def plot(self, frame: Frame) -> None:
        raise NotImplementedError

    @property
    def arrayinfo(self) -> tuple[ArrowProperties, float]:
        if self.arrows:
            return ArrowProperties(), -1.31
        return (ArrowProperties(color="grey", headwidth=0.0), -1.0)


@dataclass
class UZ(UZ_SG1_BW):
    version: Literal["v1_v2", "v3"] = "v1_v2"

    def __post_init__(self) -> None:
        if self.version == "v1_v2":
            self.margins = Margins(left=0.03, right=0.03)

    def plot(self, frame: Frame) -> None:
        top = 1.0
        denom = 4 if self.version == "v1_v2" else 2
        d_outlet2 = 0.5
        oversize = 1.2
        denom_ = 2 if self.version == "v1_v2" else 1
        points = [
            Points(
                Point(-TOL / denom, TOL),
                Point(0.5 - HOW / denom_, TOL),
                Point(0.5 - HOW / denom_, 0.0),
            ),
            Points(
                Point(0.5 + HOW / denom_, 0.0),
                Point(0.5 + HOW / denom_, TOL),
                Point(1.0, TOL),
                Point(1.0, oversize * top),
            ),
        ]
        if self.version == "v1_v2":
            points.append(
                Points(
                    Point(-TOL / denom, TOL + 4 * HOW),
                    Point(0.0, TOL + 4 * HOW),
                    Point(0.0, oversize * top),
                )
            )
        elif self.version == "v3":
            points.extend(
                (
                    Points(
                        Point(-TOL / denom, TOL + 4 * HOW),
                        Point(0.0, TOL + 4 * HOW),
                        Point(0.0, TOL + d_outlet2),
                        Point(-TOL / denom, TOL + d_outlet2),
                    ),
                    Points(
                        Point(-TOL / denom, TOL + d_outlet2 + 4 * HOW),
                        Point(0.0, TOL + d_outlet2 + 4 * HOW),
                        Point(0.0, oversize * top),
                    ),
                )
            )
        else:
            raise NotImplementedError
        self.draw_line(frame=frame, points=points, properties=LineProperties())
        self.draw_line(
            frame=frame,
            points=Points(Point(0.0, 1.0), Point(1.0, 1.0)),
            properties=LineProperties(style="dotted"),
        )
        if self.version == "v1_v2":
            self.draw_text(
                frame=frame,
                text="UZ",
                point=Point(0.5, TOL),
                properties=TextProperties(),
            )
        elif self.version == "v3":
            self.draw_text(
                frame=frame,
                text="SUZ",
                point=Point(0.5, TOL + 0.1),
                properties=TextProperties(),
            )
        else:
            raise NotImplementedError
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, 0.0),
            length=Point(0.0, -1.0),
            properties=ArrowProperties(),
        )
        if self.version == "v1_v2":
            self.draw_text(
                frame=frame,
                text="Perc",
                point=Point(0.5 + TDX / 2, -0.5),
                properties=TextProperties(horizontal="left", vertical="center"),
            )
        elif self.version == "v3":
            self.draw_text(
                frame=frame,
                text="DP",
                point=Point(0.5 + TDX, -0.5),
                properties=TextProperties(horizontal="left", vertical="center"),
            )
        else:
            raise NotImplementedError
        self.draw_arrow(
            frame=frame,
            base=Point(-TOL / denom, TOL + 2 * HOW),
            length=Point(
                self.arrayinfo[1] + (0.06 if self.version == "v1_v2" else 0.0), 0.0
            ),
            properties=self.arrayinfo[0],
        )
        if self.version == "v1_v2":
            self.draw_text(
                frame=frame,
                text="Q0",
                point=Point(-TOL / denom - 2 * TDX, TOL + 2 * HOW),
                properties=TextProperties(horizontal="right"),
            )
        elif self.arrows:
            self.draw_text(
                frame=frame,
                text="RI",
                point=Point(-1.2 * TOL + self.arrayinfo[1], TOL + 2 * HOW),
                properties=TextProperties(horizontal="center"),
            )
        elif self.version != "v3":
            raise NotImplementedError
        if self.version == "v3":
            self.draw_line(
                frame=frame,
                points=Points(Point(0.0, TOL + d_outlet2), Point(1.0, TOL + d_outlet2)),
                properties=LineProperties(style="dashed"),
            )
            if not self.arrows:
                self.draw_text(
                    frame=frame,
                    text="SGR",
                    point=Point(TDX / 2, TOL + d_outlet2),
                    properties=TextProperties(horizontal="left"),
                )
            self.draw_arrow(
                frame=frame,
                base=Point(-TOL / denom, TOL + 2 * HOW + d_outlet2),
                length=Point(self.arrayinfo[1], 0.0),
                properties=self.arrayinfo[0],
            )
            if self.arrows:
                self.draw_text(
                    frame=frame,
                    text="RS",
                    point=Point(
                        -1.2 * TOL + self.arrayinfo[1], TOL + 2 * HOW + d_outlet2
                    ),
                    properties=TextProperties(horizontal="center"),
                )


@dataclass
class LZ(Element):
    version: Literal["v1", "v2", "v4"] = "v1"

    def __post_init__(self) -> None:
        self.margins = Margins(left=0.02, right=0.02)

    def plot(self, frame: Frame) -> None:
        denom = 6
        oversize = 1.2
        if self.version in ("v1", "v4"):
            bottom = 0.0
        elif self.version == "v2":
            bottom = -1.0
        else:
            raise NotImplementedError
        self.draw_line(
            frame=frame,
            points=(
                Points(
                    Point(0.0, bottom),
                    Point(0.0, 0.5 - 2 * HOW),
                    Point(-TOL / denom, 0.5 - 2 * HOW),
                ),
                Points(
                    Point(-TOL / denom, 0.5 + 2 * HOW),
                    Point(0.0, 0.5 + 2 * HOW),
                    Point(0.0, oversize),
                ),
                Points(Point(1.0, bottom), Point(1.0, oversize)),
            ),
            properties=LineProperties(),
        )
        y = 0.8
        self.draw_line(
            frame=frame,
            points=Points(Point(0.0, y), Point(1.0, y)),
            properties=LineProperties(style="dotted"),
        )
        self.draw_text(
            frame=frame, text="LZ", point=Point(0.5, TOL), properties=TextProperties()
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5 / 3, 2.0),
            length=Point(0.0, -1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="P",
            point=Point((0.5 + TDX) / 3, 1.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.4 / 3, 1.0),
            length=Point(-0.2, 1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="EL",
            point=Point(0.3 / 3 + TDX, 1.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        if self.version in ("v1", "v2"):
            arraylength = -0.5
        elif self.version == "v4":
            arraylength = -1.5 - 2 * TOL
            self.draw_text(
                frame=frame,
                text="Q",
                point=Point(-0.65, 0.5),
                properties=TextProperties(horizontal="left"),
            )
        else:
            raise NotImplementedError
        self.draw_arrow(
            frame=frame,
            base=Point(-TOL / denom, 0.5),
            length=Point(arraylength, 0.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="Q1",
            point=Point(-TOL / denom - TDX, 0.5),
            properties=TextProperties(horizontal="right"),
        )


@dataclass
class SG1(UZ_SG1_BW):
    def plot(self, frame: Frame) -> None:
        denom = 2
        oversize = 1.2
        self.draw_line(
            frame=frame,
            points=(
                Points(
                    Point(-TOL / denom, TOL + 4 * HOW),
                    Point(0.0, TOL + 4 * HOW),
                    Point(0.0, oversize),
                ),
                Points(
                    Point(-TOL / denom, TOL),
                    Point(0.5 - HOW, TOL),
                    Point(0.5 - HOW, 0.0),
                ),
                Points(
                    Point(0.5 + HOW, 0.0),
                    Point(0.5 + HOW, TOL),
                    Point(1.0, TOL),
                    Point(1.0, oversize),
                ),
            ),
            properties=LineProperties(),
        )
        y = 0.8
        self.draw_line(
            frame=frame,
            points=Points(Point(0.0, y), Point(1.0, y)),
            properties=LineProperties(style="dotted"),
        )
        self.draw_text(
            frame=frame,
            text="SG1",
            point=Point(0.5, TOL + 0.1),
            properties=TextProperties(),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(-TOL / denom, TOL + 2 * HOW),
            length=Point(self.arrayinfo[1], 0.0),
            properties=self.arrayinfo[0],
        )
        if self.arrows:
            self.draw_text(
                frame=frame,
                text="RG1",
                point=Point(-1.2 * TOL + self.arrayinfo[1], TOL + 2 * HOW),
                properties=TextProperties(horizontal="center"),
            )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, 0.0),
            length=Point(0.0, -0.5),
            properties=ArrowProperties(headwidth=0.0),
        )
        self.draw_text(
            frame=frame,
            text="DP-GR1",
            point=Point(0.5 + TDX, -0.25),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, -0.5),
            length=Point(-0.1, -0.75),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="GR2",
            point=Point(0.45 - TDX, -0.75),
            properties=TextProperties(horizontal="right", vertical="center"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, -0.5),
            length=Point(0.1 / 0.75 * 1.75, -1.75),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="GR3",
            point=Point(0.55 + TDX, -0.75),
            properties=TextProperties(horizontal="left", vertical="center"),
        )


@dataclass
class SG23(Element):
    number: Literal[2, 3] = 2

    def __post_init__(self) -> None:
        self.margins = Margins(left=0.02, right=0.02)

    def plot(self, frame: Frame) -> None:
        denom = 6
        bottom = 0.2 if self.number == 2 else -1.0
        self.draw_line(
            frame=frame,
            points=(
                Points(
                    Point(0.0, bottom),
                    Point(0.0, 0.5 - 2 * HOW),
                    Point(0.0 - TOL / denom, 0.5 - 2 * HOW),
                ),
                Points(
                    Point(0.0 - TOL / denom, 0.5 + 2 * HOW),
                    Point(0.0 + 0.0, 0.5 + 2 * HOW),
                    Point(0.0 + 0.0, 1.0),
                ),
                Points(Point(1.0, bottom), Point(1.0, 1.0)),
            ),
            properties=LineProperties(),
        )
        y = 0.8
        self.draw_line(
            frame=frame,
            points=Points(Point(0.0, y), Point(1.0, y)),
            properties=LineProperties(style="dotted"),
        )
        self.draw_text(
            frame=frame,
            text=f"SG{self.number}",
            point=Point((0.0 + 1.0) / 2, TOL),
            properties=TextProperties(),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(-TOL / denom, 0.5),
            length=Point(-0.25 if self.number == 2 else -0.5, 0.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text=f"RG{self.number}",
            point=Point(-TOL / denom - TDX / 3, 0.5),
            properties=TextProperties(horizontal="right", vertical="bottom"),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.3 / 3, y),
            length=Point(-0.2, 1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text="EL",
            point=Point(0.18 / 3 + TDX, 1.3),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        if self.number == 2:
            self.draw_arrow(
                frame=frame,
                base=Point(0.6 / 3, 2.0),
                length=Point(0.0, -0.5),
                properties=ArrowProperties(headwidth=0.0),
            )
            self.draw_arrow(
                frame=frame,
                base=Point(0.6 / 3, 1.5),
                length=Point(-0.1, -0.75),
                properties=ArrowProperties(),
            )
            self.draw_arrow(
                frame=frame,
                base=Point(0.6 / 3, 1.5),
                length=Point(0.1 / 0.75 * 1.75, -1.75),
                properties=ArrowProperties(),
            )
            self.draw_text(
                frame=frame,
                text="P",
                point=Point((0.5 + TDX) / 3, 1.75),
                properties=TextProperties(horizontal="left", vertical="center"),
            )


@dataclass
class BW(UZ_SG1_BW):
    number: Literal[1, 2] = 1

    def plot(self, frame: Frame) -> None:
        top = 1.0
        denom = 2
        d_outlet2 = 0.5
        oversize = 1.2
        denom_ = 1
        factor = 2
        self.draw_line(
            frame=frame,
            points=(
                Points(
                    Point(0.0, oversize * top),
                    Point(0.0, TOL + d_outlet2 + factor * HOW),
                    Point(-TOL / denom, TOL + d_outlet2 + factor * HOW),
                ),
                Points(
                    Point(-TOL / denom, TOL + d_outlet2 - factor * HOW),
                    Point(0.0, TOL + d_outlet2 - factor * HOW),
                    Point(0.0, TOL),
                    Point(0.5 - HOW / denom_, TOL),
                    Point(0.5 - HOW / denom_, 0.0),
                ),
                Points(
                    Point(0.5 + HOW / denom_, 0.0),
                    Point(0.5 + HOW / denom_, TOL),
                    Point(1.0, TOL),
                    Point(1.0, oversize * top),
                ),
            ),
            properties=LineProperties(),
        )
        self.draw_line(
            frame=frame,
            points=Points(Point(0.0, 1.0), Point(1.0, 1.0)),
            properties=LineProperties(style="dotted"),
        )
        self.draw_text(
            frame=frame,
            text=f"BW{self.number}",
            point=Point(0.5, TOL),
            properties=TextProperties(),
        )
        self.draw_arrow(
            frame=frame,
            base=Point(0.5, 0.0),
            length=Point(0.0, -1.0),
            properties=ArrowProperties(),
        )
        self.draw_text(
            frame=frame,
            text=f"QVs{self.number}",
            point=Point(0.5 + TDX, -0.5),
            properties=TextProperties(horizontal="left", vertical="center"),
        )
        self.draw_line(
            frame=frame,
            points=Points(
                Point(0.0, TOL + d_outlet2 - factor * HOW),
                Point(1.0, TOL + d_outlet2 - factor * HOW),
            ),
            properties=LineProperties(style="dashed"),
        )
        if not self.arrows:
            self.draw_text(
                frame=frame,
                text=f"H{self.number}",
                point=Point(TDX / 2, TOL + d_outlet2 - factor * HOW),
                properties=TextProperties(horizontal="left"),
            )
        arraylength = self.arrayinfo[1] - 0.25 * (self.arrows and self.number == 2)
        self.draw_arrow(
            frame=frame,
            base=Point(-TOL / denom, TOL + d_outlet2),
            length=Point(arraylength, 0.0),
            properties=self.arrayinfo[0],
        )
        if self.arrows:
            self.draw_text(
                frame=frame,
                text=f"QAb{self.number}",
                point=Point(-TOL, TOL + 2 * HOW + d_outlet2),
                properties=TextProperties(horizontal="right"),
            )


class UH(Element):
    def plot(self, frame: Frame) -> None:
        self.draw_line(
            frame=frame,
            points=Points(Point(0.0, 0.0), Point(0.25, 1.0), Point(0.5, 0.0)),
            properties=LineProperties(),
        )
        self.draw_text(
            frame=frame, text="Q", point=Point(0.25, 0.25), properties=TextProperties()
        )


@dataclass
class SC(Element):
    version: Literal["v2_v3", "v4"] = "v2_v3"

    def __post_init__(self) -> None:
        self.margins = Margins(left=0.0, right=0.0)

    def plot(self, frame: Frame) -> None:
        x0 = 0.15
        if self.version == "v2_v3":
            y0 = 0.0
        elif self.version == "v4":
            y0 = 0.15
        else:
            raise NotImplementedError
        dx = 0.3
        dy = 0.65
        self.draw_line(
            frame=frame,
            points=(
                *(
                    Points(
                        Point(x0 - dx * i, y0 + 0.5 - dy * i),
                        Point(x0 - dx * i, y0 + 4 * HOW - dy * i),
                    )
                    for i in range(3)
                ),
                *(
                    Points(
                        Point(x0 - dx * i, y0 - dy * i),
                        Point(x0 + dx - dx * i, y0 - dy * i),
                        Point(x0 + dx - dx * i, y0 + 0.5 - dy * i),
                    )
                    for i in range(3)
                ),
            ),
            properties=LineProperties(),
        )
        self.draw_line(
            frame=frame,
            points=(
                *(
                    Points(
                        Point(x0 - dx * i, y0 + 0.4 - dy * i),
                        Point(x0 + dx - dx * i, y0 + 0.4 - dy * i),
                    )
                    for i in range(3)
                ),
            ),
            properties=LineProperties(style="dotted"),
        )
        for i in range(3):
            self.draw_text(
                frame=frame,
                text="SC",
                point=Point(dx - dx * i, y0 + -dy * i),
                properties=TextProperties(vertical="bottom"),
            )
        for i in range(2):
            self.draw_arrow(
                frame=frame,
                base=Point(x0 - dx * i, y0 + 0.1 - dy * i),
                length=Point(-0.225 / 1.5, -0.45 / 1.5),
                properties=ArrowProperties(),
            )
        i = 2
        if self.version == "v2_v3":
            self.draw_arrow(
                frame=frame,
                base=Point(x0 - dx * i, y0 + 0.1 - dy * i),
                length=Point(-0.3, 0.0),
                properties=ArrowProperties(),
            )
            self.draw_text(
                frame=frame,
                text="Q",
                point=Point(x0 - dx * i - 4 * TDX, y0 + 0.1 - dy * i),
                properties=TextProperties(vertical="bottom", horizontal="right"),
            )
        elif self.version == "v4":
            self.draw_arrow(
                frame=frame,
                base=Point(x0 - dx * i, y0 + 0.1 - dy * i),
                length=Point(-0.225, -0.45),
                properties=ArrowProperties(headwidth=0.0),
            )
        else:
            raise NotImplementedError


@dataclass
class Frame:
    grid: Grid
    margins: Margins
    elements: Sequence[Element]
    xfactor: float = 2.0
    yfactor: float = 0.5

    def plot(self, filename: Optional[str] = None) -> None:
        for e in self.elements:
            e.plot(frame=self)
        fig = pyplot.gcf()
        fig.subplots_adjust(bottom=0)
        fig.subplots_adjust(top=1)
        fig.subplots_adjust(right=1)
        fig.subplots_adjust(left=0)
        fig.set_size_inches(
            self.xfactor * self.grid.ncols, self.yfactor * self.grid.nrows
        )
        if filename is None:
            pyplot.show()
        else:
            pyplot.savefig(os.path.join("figs", filename))
        pyplot.clf()


if __name__ == "__main__":
    elements_hland_v1_v2 = [
        Edge(index=Index(i0=0, i1=10, j0=0, j1=3)),
        Title(index=Index(i0=10, j0=0), text="SEALED"),
        Title(index=Index(i0=10, j0=1), text="INTERNAL LAKE"),
        Title(index=Index(i0=10, j0=2), text="GLACIER"),
        Title(index=Index(i0=10, j0=3), text="FIELD/FOREST"),
        Interception(Index(i0=8, j0=0)),
        Interception(Index(i0=8, j0=3)),
        Snow(Index(i0=6, j0=0), arrowfactor=5.5, include_sr=True),
        Snow(Index(i0=6, j0=2), arrowfactor=3.0),
        Snow(Index(i0=6, j0=3)),
        Soil(Index(i0=4, j0=3)),
        Glacier(Index(i0=4, j0=2)),
        UZ(Index(i0=2, j0=2, j1=3)),
        LZ(Index(i0=0, j0=1, j1=3)),
    ]
    elements_hland_v1 = elements_hland_v1_v2 + [UH(Index(i0=0, j0=0))]
    Frame(
        grid=Grid(nrows=11, ncols=4), margins=Margins(), elements=elements_hland_v1
    ).plot("HydPy-H-Land_Version-1.png")

    elements_hland_v2 = elements_hland_v1_v2 + [SC(Index(i0=0, j0=0))]
    for element in elements_hland_v2:
        if element.index.i1 is not None:
            element.index.i1 += 1
        if element.index.j1 is not None:
            element.index.j1 += 1
        if isinstance(element, Edge):
            continue
        element.index.i0 += 1
        element.index.j0 += 1
        if isinstance(element, LZ):
            element.version = "v2"
    Frame(
        grid=Grid(nrows=12, ncols=5), margins=Margins(), elements=elements_hland_v2
    ).plot("HydPy-H-Land_Version-2.png")

    elements_hland_v3 = [e for e in elements_hland_v2 if not isinstance(e, (UZ, LZ))]
    for idx, element in enumerate(elements_hland_v3):
        if isinstance(element, SC):
            continue
        if element.index.i1 is not None:
            element.index.i1 += 3
        if isinstance(element, Edge):
            continue
        element.index.i0 += 3
        if isinstance(element, Snow) and element.index.j0 == 1:
            element.arrowfactor = 8.5
        if isinstance(element, Soil):
            element.version = "v3_v4"
    elements_hland_v3.extend(
        (
            UZ(Index(i0=6, j0=3), version="v3"),
            UZ(Index(i0=6, j0=4), version="v3", arrows=False),
            SG1(Index(i0=4, j0=3)),
            SG1(Index(i0=4, j0=4), arrows=False),
            SG23(Index(i0=2, j0=2, j1=4), number=2),
            SG23(Index(i0=1, j0=2, j1=4), number=3),
        )
    )
    Frame(
        grid=Grid(nrows=15, ncols=5), margins=Margins(), elements=elements_hland_v3
    ).plot("HydPy-H-Land_Version-3.png")

    elements_hland_v4 = [
        e for e in elements_hland_v3 if not isinstance(e, (UZ_SG1_BW, SG23))
    ]
    for element in elements_hland_v4:
        if isinstance(element, SC):
            element.version = "v4"
            element.index.i0 = 2
            continue
        if element.index.i1 is not None:
            element.index.i1 -= 2
        if isinstance(element, Edge):
            continue
        element.index.i0 -= 2
        if isinstance(element, Snow) and element.index.j0 == 1:
            element.arrowfactor = 5.25
    elements_hland_v4.extend(
        (
            BW(Index(i0=4, j0=3)),
            BW(Index(i0=4, j0=4), number=1, arrows=False),
            BW(Index(i0=2, j0=3), number=2),
            BW(Index(i0=2, j0=4), number=2, arrows=False),
            LZ(Index(i0=0, j0=2, j1=4), version="v4"),
        )
    )
    Frame(
        grid=Grid(nrows=13, ncols=5), margins=Margins(), elements=elements_hland_v4
    ).plot("HydPy-H-Land_Version-4.png")
