# navyfox._proxy — proxy base and descriptor machinery
from navyfox._proxy.base import ProxyBase
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
    "BoolProperty",
    "IntProperty",
    "StringProperty",
    "FloatProperty",
    "ChoiceProperty",
    "ColorProperty",
    "ObjectProperty",
]
