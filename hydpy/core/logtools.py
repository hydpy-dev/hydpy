# -*- coding: utf-8 -*-
"""This module implements classes for logging variables during simulation runs.

All features of module |logtools| are experimental at the moment.  It is
very likely that their interfaces will change significantly in the future.
"""
# import...
# ...from standard library
from __future__ import annotations
from typing import *
from typing import TextIO

# ...from HydPy
from hydpy.core import timetools
import hydpy

if TYPE_CHECKING:
    from hydpy.core import sequencetools


class BaseLogger:
    """Base class for all logging classes."""

    def __init__(
        self,
        firstdate: Optional[timetools.DateConstrArg] = None,
        lastdate: Optional[timetools.DateConstrArg] = None,
    ):
        if firstdate is None:
            self._firstdate = hydpy.pub.timegrids.init.firstdate
        else:
            self._firstdate = timetools.Date(firstdate)
        if lastdate is None:
            self._lastdate = hydpy.pub.timegrids.init.lastdate
        else:
            self._lastdate = timetools.Date(lastdate)
        self._idx0 = hydpy.pub.timegrids.init[self._firstdate]
        self._idx1 = hydpy.pub.timegrids.init[self._lastdate]


class Logger(BaseLogger):
    """Logger for sums of a single period."""

    counter: int
    sequence2sum: Dict[sequencetools.Sequence_, float]

    def __init__(
        self,
        firstdate: Optional[timetools.DateConstrArg] = None,
        lastdate: Optional[timetools.DateConstrArg] = None,
    ) -> None:
        super().__init__(firstdate=firstdate, lastdate=lastdate)
        self.counter = 0
        self.sequence2sum = {}

    def add_sequence(self, sequence: sequencetools.Sequence_) -> None:
        """Add a |Sequence| object to the current |Logger| object."""
        self.sequence2sum[sequence] = 0.0

    def update(self, idx: int) -> None:
        """Sum the values of all addes sequences."""
        if self._idx0 <= idx < self._idx1:
            self.counter += 1
            for sequence in self.sequence2sum.keys():
                self.sequence2sum[sequence] += sequence.value

    @property
    def sequence2mean(self) -> Dict[sequencetools.Sequence_, float]:
        """Dictionary containing the logged mean values instead of the
        original logged sums."""
        return {seq: sum_ / self.counter for seq, sum_ in self.sequence2sum.items()}


class MonthLogger(BaseLogger):
    """Logger for monthly sums."""

    month2counter: Dict[str, int]
    month2sequence2sum: Dict[str, Dict[sequencetools.Sequence_, float]]

    def __init__(
        self,
        firstdate: Optional[timetools.DateConstrArg] = None,
        lastdate: Optional[timetools.DateConstrArg] = None,
    ) -> None:
        super().__init__(firstdate=firstdate, lastdate=lastdate)
        self.month2counter = {}
        self.month2sequence2sum = {}
        date: timetools.Date
        lastmonth = ""
        for date in timetools.Timegrid(
            self._firstdate, self._lastdate, hydpy.pub.timegrids.stepsize
        ):
            nextmonth = self.date2month(date)
            if nextmonth != lastmonth:
                self.month2counter[nextmonth] = 0
                self.month2sequence2sum[nextmonth] = {}
                lastmonth = nextmonth

    @staticmethod
    def date2month(date):
        """Convert a |Date| object to a "year-month" string."""
        return f'{date.year}-{str(date.month).rjust(2, "0")}'

    def add_sequence(self, sequence: sequencetools.Sequence_) -> None:
        """Add a |Sequence| object to the current |Logger| object."""
        for sequence2sum in self.month2sequence2sum.values():
            sequence2sum[sequence] = 0.0

    def update(self, idx: int) -> None:
        """Sum the values of all addes sequences."""
        if self._idx0 <= idx < self._idx1:
            month = self.date2month(hydpy.pub.timegrids.init[idx])
            self.month2counter[month] += 1
            sequence2sum = self.month2sequence2sum[month]
            for sequence in sequence2sum.keys():
                sequence2sum[sequence] += sequence.value

    @property
    def month2sequence2mean(self) -> Dict[str, Dict[sequencetools.Sequence_, float]]:
        """Nested dictionary containing the logged mean values instead of
        the original logged sums."""
        month2sequence2mean = {}
        for month, sequence2sum in self.month2sequence2sum.items():
            counter = self.month2counter[month]
            month2sequence2mean[month] = self._apply_factor(sequence2sum, 1.0 / counter)
        return month2sequence2mean

    @staticmethod
    def _apply_factor(
        sequence2value: Dict[sequencetools.Sequence_, float],
        factor: float,
    ) -> Dict[sequencetools.Sequence_, float]:
        return {seq: factor * sum_ for seq, sum_ in sequence2value.items()}

    def apply_factor(
        self,
        month2sequence2value: Dict[str, Dict[sequencetools.Sequence_, float]],
        factor: float,
    ) -> Dict[str, Dict[sequencetools.Sequence_, float]]:
        """Remove?"""
        month2sequence2newvalue = {}
        for month, sequence2value in month2sequence2value.items():
            month2sequence2newvalue[month] = self._apply_factor(sequence2value, factor)
        return month2sequence2newvalue

    @staticmethod
    def write_seriesfile(
        seriesfile: TextIO,
        month2sequence2value: Dict[str, Dict[sequencetools.Sequence_, float]],
    ) -> None:
        """Write the averaged values of the given nested dictionary to the
        given file.

        We assume equal weights (e.g. areas) for all values.  Needs improvement.
        """
        for month, sequence2value in sorted(month2sequence2value.items()):
            spatialmean = sum(sequence2value.values()) / len(sequence2value)
            seriesfile.write(f"{month}\t{spatialmean}\n")
