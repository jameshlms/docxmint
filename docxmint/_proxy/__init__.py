# docxmint._proxy — proxy base and descriptor machinery
from docxmint._attrs import RawAttrMixin
from docxmint._proxy.base import UNSET, ProxyBase
from docxmint._proxy.descriptors import (
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
