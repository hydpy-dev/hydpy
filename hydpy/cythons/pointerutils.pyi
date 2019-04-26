

class DoubleBase:
    ...


class Double(DoubleBase):

    def __init__(self, value: float):
        ...

    def __getitem__(self, key: int) -> float:
        ...

    def __setitem__(self, key: int, value: float) -> None:
        ...


class PDouble(DoubleBase):
    ...


class PPDouble:
    ...
