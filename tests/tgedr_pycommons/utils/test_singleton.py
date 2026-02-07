import logging
import pytest
from tgedr_pycommons.utils.singleton import SingletonMeta


logger = logging.getLogger(__name__)


def test_singleton_creates_single_instance():
    """Test that SingletonMeta ensures only one instance is created."""
    
    class TestClass(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value
    
    obj1 = TestClass(10)
    obj2 = TestClass(20)
    
    assert obj1 is obj2
    assert obj1.value == 10  # Value from first instantiation


def test_singleton_different_classes_have_different_instances():
    """Test that different classes using SingletonMeta have separate instances."""
    
    class ClassA(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value
    
    class ClassB(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value
    
    obj_a1 = ClassA(10)
    obj_a2 = ClassA(20)
    obj_b1 = ClassB(30)
    obj_b2 = ClassB(40)
    
    # Same class instances should be identical
    assert obj_a1 is obj_a2
    assert obj_b1 is obj_b2
    
    # Different class instances should be different
    assert obj_a1 is not obj_b1
    
    # Values should be from first instantiation
    assert obj_a1.value == 10
    assert obj_b1.value == 30


def test_singleton_with_no_args():
    """Test singleton pattern with no constructor arguments."""
    
    class NoArgsClass(metaclass=SingletonMeta):
        def __init__(self):
            self.counter = 0
    
    obj1 = NoArgsClass()
    obj1.counter = 5
    
    obj2 = NoArgsClass()
    
    assert obj1 is obj2
    assert obj2.counter == 5


def test_singleton_with_kwargs():
    """Test singleton pattern with keyword arguments."""
    
    class KwargsClass(metaclass=SingletonMeta):
        def __init__(self, name=None, age=None):
            self.name = name
            self.age = age
    
    obj1 = KwargsClass(name="Alice", age=30)
    obj2 = KwargsClass(name="Bob", age=25)
    
    assert obj1 is obj2
    assert obj1.name == "Alice"
    assert obj1.age == 30


def test_singleton_with_mixed_args_kwargs():
    """Test singleton pattern with both positional and keyword arguments."""
    
    class MixedArgsClass(metaclass=SingletonMeta):
        def __init__(self, value, multiplier=2):
            self.value = value
            self.multiplier = multiplier
    
    obj1 = MixedArgsClass(10, multiplier=3)
    obj2 = MixedArgsClass(20, multiplier=5)
    
    assert obj1 is obj2
    assert obj1.value == 10
    assert obj1.multiplier == 3


def test_singleton_state_persistence():
    """Test that state changes persist across references."""
    
    class StatefulClass(metaclass=SingletonMeta):
        def __init__(self):
            self.items = []
        
        def add_item(self, item):
            self.items.append(item)
    
    obj1 = StatefulClass()
    obj1.add_item("first")
    
    obj2 = StatefulClass()
    obj2.add_item("second")
    
    # Both references should see all items
    assert obj1 is obj2
    assert len(obj1.items) == 2
    assert len(obj2.items) == 2
    assert obj1.items == ["first", "second"]


def test_singleton_inheritance():
    """Test singleton behavior with class inheritance."""
    
    class ParentSingleton(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value
    
    class ChildSingleton(ParentSingleton):
        def __init__(self, value, extra):
            super().__init__(value)
            self.extra = extra
    
    parent1 = ParentSingleton(10)
    parent2 = ParentSingleton(20)
    
    child1 = ChildSingleton(30, "extra1")
    child2 = ChildSingleton(40, "extra2")
    
    # Parent instances should be the same
    assert parent1 is parent2
    assert parent1.value == 10
    
    # Child instances should be the same
    assert child1 is child2
    assert child1.value == 30
    assert child1.extra == "extra1"
    
    # Parent and child should be different instances
    assert parent1 is not child1


def test_singleton_with_mutable_default_args():
    """Test singleton with mutable default arguments."""
    
    class MutableDefaultClass(metaclass=SingletonMeta):
        def __init__(self, items=None):
            self.items = items if items is not None else []
    
    obj1 = MutableDefaultClass([1, 2, 3])
    obj2 = MutableDefaultClass([4, 5, 6])
    
    assert obj1 is obj2
    assert obj1.items == [1, 2, 3]


def test_singleton_with_complex_initialization():
    """Test singleton with complex initialization logic."""
    
    class ComplexClass(metaclass=SingletonMeta):
        def __init__(self, config):
            self.config = config
            self.initialized = True
            self.setup()
        
        def setup(self):
            self.data = {"key": self.config}
    
    config1 = {"setting": "value1"}
    obj1 = ComplexClass(config1)
    
    config2 = {"setting": "value2"}
    obj2 = ComplexClass(config2)
    
    assert obj1 is obj2
    assert obj1.config == config1
    assert obj1.data == {"key": config1}


def test_singleton_thread_safety_basic():
    """Test basic singleton behavior that should work in single-threaded context."""
    
    class CounterClass(metaclass=SingletonMeta):
        def __init__(self):
            self.count = 0
        
        def increment(self):
            self.count += 1
    
    obj1 = CounterClass()
    obj1.increment()
    
    obj2 = CounterClass()
    obj2.increment()
    
    assert obj1 is obj2
    assert obj1.count == 2
    assert obj2.count == 2
