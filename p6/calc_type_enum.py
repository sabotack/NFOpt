from enum import Enum


class CalcType(Enum):
    BASELINE = "baseline"
    AVERAGE = "average"
    MAX = "max"
    SQUARED = "squared"
    RATIOS = "ratios"
