"""Metaclass implementation for the Singleton design pattern.

This module provides a SingletonMeta metaclass that ensures only one instance
of a class using this metaclass exists.
"""

from typing import ClassVar


class SingletonMeta(type):
    """Metaclass for implementing the Singleton pattern.

    Ensures that only one instance of a class using this metaclass exists.
    The metaclass maintains a dictionary of instances and returns the same
    instance when the class is instantiated multiple times.

    Example:
        >>> class MyClass(metaclass=SingletonMeta):
        ...     def __init__(self, value):
        ...         self.value = value
        ...
        >>> obj1 = MyClass(10)
        >>> obj2 = MyClass(20)
        >>> obj1 is obj2
        True
        >>> obj1.value  # Note: value is from first instantiation
        10
    """

    _instances: ClassVar[dict[type, object]] = {}

    def __call__(cls, *args, **kwargs) -> object:  # noqa: ANN002, ANN003
        """Create or return the singleton instance of the class.

        If an instance of the class already exists, return it. Otherwise,
        create a new instance, store it, and return it.

        Args:
            *args: Positional arguments passed to the class constructor.
            **kwargs: Keyword arguments passed to the class constructor.

        Returns:
            object: The singleton instance of the class.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
