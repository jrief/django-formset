from enum import auto

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


class ClassList(set):
    """
    Inspired by JavaScript's classlist on HTMLElement
    """
    __slots__ = ()

    def __init__(self, css_classes=None):
        if css_classes is None:
            super().__init__()
        elif isinstance(css_classes, (list, set, tuple)):
            super().__init__(css_classes)
        elif isinstance(css_classes, str):
            super().__init__(css_classes.split())
        else:
            raise TypeError(f"Can not convert {css_classes.__class__} to ClassList")

    def __bool__(self):
        return len(self) > 0

    def add(self, css_classes):
        for css_class in ClassList(css_classes):
            super().add(css_class)
        return self

    def remove(self, css_classes):
        for css_class in ClassList(css_classes):
            if css_class in self:
                super().remove(css_class)
        return self

    def toggle(self, css_classes, condition=None):
        for css_class in ClassList(css_classes):
            if css_class in self:
                if condition in (None, False):
                    super().remove(css_class)
            else:
                if condition in (None, True):
                    super().add(css_class)
        return self

    def render(self):
        return ' '.join(self)

    __str__ = render
    __html__ = render


class ButtonVariant(StrEnum):
    PRIMARY = auto()
    SECONDARY = auto()
    SUCCESS = auto()
    DANGER = auto()
    WARNING = auto()
    INFO = auto()
