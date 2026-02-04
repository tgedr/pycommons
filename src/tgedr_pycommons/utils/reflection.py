"""Reflection utilities for dynamic class loading and discovery."""

import importlib
import inspect
import logging
import os
import sys
from importlib import import_module
from typing import Any


logger = logging.getLogger(__name__)


class UtilsReflectionException(Exception):
    """Exception raised by reflection utilities."""


class UtilsReflection:
    """Utility class for reflection operations including class loading and discovery."""

    __MODULE_EXTENSIONS = (".py", ".pyc", ".pyo")

    @staticmethod
    def load_class(clazz: str, parent_check: type | None = None) -> Any:
        """Load a class dynamically from a fully qualified class name.

        Args:
            clazz: Fully qualified class name (e.g., 'module.submodule.ClassName').
            parent_check: Optional parent class to validate against.

        Returns:
            The loaded class.

        Raises:
            TypeError: If the object is not callable or not a subclass of parent_check.
        """
        logger.debug("[load_class|in] (clazz=%s, parent_check=%s)", clazz, parent_check)
        type_elements = clazz.split(".")
        module = ".".join(type_elements[:-1])
        _clazz = type_elements[-1]

        result = getattr(import_module(module), _clazz)

        if not callable(result):
            msg = f"Object {_clazz} in {module} is not callable."
            raise TypeError(msg)

        if parent_check and (not issubclass(result, parent_check)):
            msg = f"Wrong class type, it is not a subclass of {parent_check.__name__}"
            raise TypeError(msg)

        logger.debug("[load_class|out] => %s", result)
        return result

    @staticmethod
    def load_subclass_from_module(module: str, clazz: str, super_clazz: type) -> Any:
        """Load a subclass from a module.

        Args:
            module: Module name to load from.
            clazz: Class name to load.
            super_clazz: Parent class that the loaded class must inherit from.

        Returns:
            The loaded class.

        Raises:
            TypeError: If the object is not callable or not a subclass of super_clazz.
        """
        logger.info("[load_subclass_from_module|in] (module=%s, clazz=%s, super_clazz=%s)", module, clazz, super_clazz)
        result = getattr(import_module(module), clazz)

        if not callable(result):
            msg = f"Object {clazz} in {module} is not callable."
            raise TypeError(msg)

        if super_clazz and (not issubclass(result, super_clazz)):
            msg = f"Wrong class type, it is not a subclass of {super_clazz.__name__}"
            raise TypeError(msg)

        logger.info("[load_subclass_from_module|out] => %s", result)
        return result

    @staticmethod
    def get_type(module: str, _type: str) -> type:
        """Get a type from a module by name.

        Args:
            module: Module name.
            _type: Type name to retrieve.

        Returns:
            The requested type.
        """
        logger.info("[get_type|in] (module=%s, _type=%s)", module, _type)
        result = None

        result = getattr(import_module(module), _type)

        logger.info("[get_type|out] => %s", result)
        return result

    @staticmethod
    def is_subclass_of(sub_class: type, super_class: type) -> bool:
        """Check if sub_class is a subclass of super_class.

        Args:
            sub_class: The class to check.
            super_class: The parent class to check against.

        Returns:
            True if sub_class is a subclass of super_class, False otherwise.
        """
        logger.info("[is_subclass_of|in] (%s, %s)", sub_class, super_class)
        result = False

        if callable(sub_class) and issubclass(sub_class, super_class):
            result = True

        logger.info("[is_subclass_of|out] => %s", result)
        return result

    @staticmethod
    def find_module_classes(module: str) -> list[Any]:
        """Find all classes defined in a module.

        Args:
            module: Module name to search.

        Returns:
            List of classes found in the module.
        """
        logger.info("[find_module_classes|in] (%s)", module)
        result = []
        for _, obj in inspect.getmembers(sys.modules[module]):
            if inspect.isclass(obj):
                result.append(obj)
        logger.info("[find_module_classes|out] => %s", result)
        return result

    @staticmethod
    def find_class_implementations_in_package(package_name: str, super_class: type) -> dict[str, type]:
        """Find all implementations of a class in a package.

        Args:
            package_name: Package name to search.
            super_class: Parent class to find implementations of.

        Returns:
            Dictionary mapping module names to class implementations.
        """
        logger.info("[find_class_implementations_in_package|in] (%s, %s)", package_name, super_class)
        result = {}

        the_package = importlib.import_module(package_name)
        pkg_path = the_package.__path__[0]
        modules = [
            package_name + "." + module.split(".")[0]
            for module in os.listdir(pkg_path)
            if module.endswith(UtilsReflection.__MODULE_EXTENSIONS) and module != "__init__.py"
        ]

        logger.info("[find_class_implementations_in_package] found modules: %s", modules)

        for _module in modules:
            if _module not in sys.modules:
                importlib.import_module(_module)

            for _class in UtilsReflection.find_module_classes(_module):
                if UtilsReflection.is_subclass_of(_class, super_class) and _class != super_class:
                    result[_module] = _class

        logger.info("[find_class_implementations_in_package|out] => %s", result)
        return result

    @staticmethod
    def find_package_path(package_name: str) -> str:
        """Find the file system path of a package.

        Args:
            package_name: Package name to locate.

        Returns:
            File system path to the package.
        """
        logger.info("[find_package_path|in] (%s)", package_name)
        the_package = importlib.import_module(package_name)
        result = the_package.__path__[0]
        logger.info("[find_package_path|out] => %s", result)
        return result

    @staticmethod
    def find_class_implementations(packages: str, clazz: Any) -> dict[str, Any]:
        """Find class implementations across multiple packages.

        Args:
            packages: Comma-separated list of package names.
            clazz: Parent class to find implementations of.

        Returns:
            Dictionary mapping implementation names to classes.

        Raises:
            UtilsReflectionException: If an error occurs during discovery.
        """
        logger.info("[find_class_implementations|in] (%s, %s)", packages, clazz)
        result = {}
        _packages = [a.strip() for a in packages.split(",")]

        # find classes that extend clazz
        for pack_name in _packages:
            module_class_map = UtilsReflection.find_class_implementations_in_package(pack_name, clazz)
            for mod, _clazz in module_class_map.items():
                impl = mod.split(".")[-1]
                result[impl] = _clazz

        logger.info("[find_class_implementations|out] => %s", result)
        return result
