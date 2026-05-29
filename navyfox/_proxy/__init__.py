# navyfox._proxy — proxy base and descriptor machinery
from navyfox._attrs import RawAttrMixin
from navyfox._proxy.base import UNSET, ProxyBase
from navyfox._proxy.descriptors import (
    BoolProperty,
    ChoiceProperty,
    ColorProperty,
    FloatProperty,
    IntProperty,
    ObjectProperty,
    StringProperty,
)

__all__ = [
    "ProxyBase",
    "UNSET",
    "RawAttrMixin",
    "BoolProperty",
    "IntProperty",
    "StringProperty",
    "FloatProperty",
    "ChoiceProperty",
    "ColorProperty",
    "ObjectProperty",
]
