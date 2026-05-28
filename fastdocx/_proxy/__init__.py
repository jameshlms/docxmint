# fastdocx._proxy — proxy base and descriptor machinery
from fastdocx._attrs import RawAttrMixin
from fastdocx._proxy.base import UNSET, ProxyBase
from fastdocx._proxy.descriptors import (
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
