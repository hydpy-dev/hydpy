

class DoubleBase:

    def __float__(self) -> float:
        ...


class Double(DoubleBase):

    def __init__(self, value: float):
        ...

    def __getitem__(self, key: int) -> float:
        ...

    def __setitem__(self, key: int, value: float) -> None:
        ...


class PDouble(DoubleBase):

    def __init__(self, value: Double):
        ...


class PPDouble:
    ...

    def set_pointer(self, value: Double, idx: int):
        ...
