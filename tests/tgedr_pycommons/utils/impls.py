import abc
from typing import Any, Dict, Optional

class Sink(abc.ABC):

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config

    @abc.abstractmethod
    def put(self, context: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError

class Source(abc.ABC):

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config

    @abc.abstractmethod
    def get(self, context: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError

    
class ASink(Sink):
    def put(self, context: Optional[Dict[str, Any]] = None) -> Any:
        pass


class ASource(Source):
    def get(self, context: Optional[Dict[str, Any]] = None) -> Any:
        pass


class NotASource:
    def getX(self, context: Optional[Dict[str, Any]] = None) -> Any:
        pass


# Non-callable attribute for testing
NOT_A_CLASS = "this_is_not_a_class"


# Non-callable attribute for testing
NOT_A_CLASS = "this_is_not_a_class"
