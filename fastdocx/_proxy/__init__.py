# fastdocx._proxy — proxy base and descriptor machinery
from fastdocx._attrs import RawAttrMixin
from fastdocx._proxy.base import ProxyBase
from fastdocx._proxy.descriptors import (
    BoolProperty,
    ChoiceProperty,
    ColorProperty,
    FloatProperty,
    ObjectProperty,
    StringProperty,
)

__all__ = [
    "ProxyBase",
    "RawAttrMixin",
    "BoolProperty",
    "StringProperty",
    "FloatProperty",
    "ChoiceProperty",
    "ColorProperty",
    "ObjectProperty",
]
