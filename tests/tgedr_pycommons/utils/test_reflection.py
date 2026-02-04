import logging
import os
import pytest
from tgedr_pycommons.utils.reflection import UtilsReflection
from tests.tgedr_pycommons.utils.impls import ASource, Sink, Source


logger = logging.getLogger(__name__)

MODULE = "tests.tgedr_pycommons.utils.impls"


def test_load_subclass_from_module():
    assert UtilsReflection.load_subclass_from_module(MODULE, "ASource", Source) is not None


def test_load_class():
    assert type(UtilsReflection.load_class(MODULE + "." + "ASource", Source)) == type(ASource)


def test_load_class_no_parent_check():
    assert type(UtilsReflection.load_class(MODULE + "." + "ASource")) == type(ASource)


def test_load_subclass_from_module_attribute_error():
    with pytest.raises(AttributeError):
        UtilsReflection.load_subclass_from_module(MODULE, "SourceImplMissing", Source)


def test_load_class_from_module_type_error1():
    with pytest.raises(TypeError):
        UtilsReflection.load_subclass_from_module(MODULE, "ASink", Source)


def test_load_class_from_module_type_error2():
    with pytest.raises(TypeError):
        UtilsReflection.load_subclass_from_module(MODULE, "NotASource", Source)


def test_get_type():
    assert UtilsReflection.get_type(MODULE, "ASink") is not None


def test_is_subclass_of():
    o = UtilsReflection.get_type(MODULE, "ASink")
    assert UtilsReflection.is_subclass_of(o, Sink)


def test_is_subclass_of_not():
    o = UtilsReflection.get_type(MODULE, "ASink")
    assert not UtilsReflection.is_subclass_of(o, Source)


def test_find_module_classes():
    assert any(
        elem in [x.__name__ for x in UtilsReflection.find_module_classes(MODULE)]
        for elem in ["ASink", "ASource", "NotASource"]
    )


def test_find_module_classes_and_create_one():
    the_class = None
    classes = UtilsReflection.find_module_classes(MODULE)
    for clazz in classes:
        if clazz.__name__ == "ASink":
            the_class = clazz
            break
    assert UtilsReflection.is_subclass_of(the_class, Sink)
    dummy = the_class()
    assert dummy is not None


def test_find_package_folder():
    from tests.tgedr_pycommons.utils.impls import __file__ as f

    expected = os.path.dirname(os.path.abspath(f))
    assert expected == UtilsReflection.find_package_path("tests.tgedr_pycommons.utils")

def test_find_class_implementations():
    assert 1 == len(
        set(UtilsReflection.find_class_implementations(packages="tests.tgedr_pycommons.utils", clazz=Source).values())
    )


def test_load_class_not_callable():
    """Test loading a non-callable object raises TypeError in load_class"""
    with pytest.raises(TypeError, match="is not callable"):
        UtilsReflection.load_class(MODULE + ".NOT_A_CLASS")


def test_load_class_wrong_parent():
    """Test loading a class with wrong parent type raises TypeError in load_class"""
    with pytest.raises(TypeError, match="Wrong class type"):
        UtilsReflection.load_class(MODULE + ".ASink", Source)


def test_load_subclass_from_module_not_callable():
    """Test loading a non-callable object raises TypeError in load_subclass_from_module"""
    with pytest.raises(TypeError, match="is not callable"):
        UtilsReflection.load_subclass_from_module(MODULE, "NOT_A_CLASS", Source)


def test_load_class_not_callable():
    """Test loading a non-callable object raises TypeError in load_class"""
    with pytest.raises(TypeError, match="is not callable"):
        UtilsReflection.load_class(MODULE + ".NOT_A_CLASS")


def test_load_class_wrong_parent():
    """Test loading a class with wrong parent type raises TypeError in load_class"""
    with pytest.raises(TypeError, match="Wrong class type"):
        UtilsReflection.load_class(MODULE + ".ASink", Source)


def test_load_subclass_from_module_not_callable():
    """Test loading a non-callable object raises TypeError in load_subclass_from_module"""
    with pytest.raises(TypeError, match="is not callable"):
        UtilsReflection.load_subclass_from_module(MODULE, "NOT_A_CLASS", Source)
