"""Unit tests for the entrypoint module."""

import json

from tgedr_pycommons.cicd.entrypoint import entrypoint, parse_arguments



MODULE = "tests.tgedr_pycommons.classes"


def test_parse_arguments(): # noqa: ANN201, D103
  o = parse_arguments(["--module", MODULE, "--callable", "hello", "--params", '{"x": 1, "y": 2}'])

  assert o.module == MODULE
  assert o.callable == "hello"
  params = json.loads(o.params)
  assert params["x"] == 1
  assert params["y"] == 2


def test_entrypoint_function(): # noqa: ANN201, D103
  assert "hello. url: http://mybucket/mykey" == entrypoint(
  [
  "--module",
  MODULE,
  "--callable",
  "hello",
  "--params",
  '{"url": "http://mybucket/mykey"}',
  ]
  )


def test_entrypoint_function_no_params(): # noqa: ANN201, D103
  assert "hello." == entrypoint(["--module", MODULE, "--callable", "hello"])


def test_entrypoint_class_init_config_plus_run_function_with_params(): # noqa: ANN201, D103
  assert "hello. zero: zero one: one two: two" == entrypoint(
  [
  "--module",
  MODULE,
  "--classname",
  "AClass",
  "--classparams",
  '{ "config": {"zero": "zero"} }',
  "--callable",
  "getx",
  "--params",
  '{ "context": {"one": "one", "two": "two"} }',
  ]
  )


def test_entrypoint_class_run_function_with_params(): # noqa: ANN201, D103
  assert "hello. n: n" == entrypoint(
  ["--module", MODULE, "--classname", "AClass", "--callable", "gety", "--params", '{ "n": "n" }']
  )


def test_entrypoint_class_run_function_with_no_params(): # noqa: ANN201, D103
  assert "hello." == entrypoint(["--module", MODULE, "--classname", "AClass", "--callable", "gety2"])


def test_entrypoint_class_run_function_with_null_params(): # noqa: ANN201, D103
  assert "hello." == entrypoint(
  ["--module", MODULE, "--classname", "AClass", "--callable", "gety", "--params", '{ "n": null }']
  )
