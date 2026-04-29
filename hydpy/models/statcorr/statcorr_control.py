class AriNQ(parametertools.Parameter):
    """Average size of the water surface [km²]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)
