"""Module containing classes for testing purposes."""
from typing import Any # noqa: D100


class AClass: # noqa: D101
  def __init__(self, config: dict[str, Any] | None = None): # noqa: ANN204, D107
    self._config = config

  def getx(self, context: dict[str, Any] | None = None, **kwargs) -> Any: # noqa: ANN003, ARG002, D102
    msg = "hello."
    if self._config and ("zero" in self._config):
      msg += f" zero: {self._config['zero']}"
    if "one" in context:
      msg += f" one: {context['one']}"
    if "two" in context:
      msg += f" two: {context['two']}"
    return msg
    
  def gety(self, n: str | None) -> Any: # noqa: D102
      msg = "hello."
      if n:
        msg += f" n: {n}"
      return msg

  def gety2(self) -> Any: # noqa: D102
    return "hello."


def hello(*args: Any, **kwargs: Any) -> Any:
  """A simple function to return a greeting."""
  msg = "hello."
  for arg in args:
    msg += f" {arg}"
  for key, value in kwargs.items():
    msg += f" {key}: {value}"
  return msg
