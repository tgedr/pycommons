"""Module for executing Python callables based on command line arguments.

This module provides utilities to:
- Parse command line arguments for callable execution
- Resolve callables (functions or class methods) from module paths
- Execute the resolved callable with provided parameters
"""

import argparse
from collections.abc import Sequence
from argparse import Namespace
import json
import logging
from importlib import import_module
from typing import Any


root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] => %(message)s")
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)


def parse_arguments(explicit_args: Sequence[str] | None = None) -> Namespace:
    """Parse command line arguments for the python callable execution.

    Args:
      explicit_args: A sequence of command line arguments
    Returns:
      Namespace: The parsed command line arguments

    """
    parser = argparse.ArgumentParser(description="Get the parameters for the python callable to execute.")
    parser.add_argument("--module", type=str, help="The module where to find the callable")
    parser.add_argument("--callable", type=str, help="The callable (function or class function)")
    parser.add_argument(
        "--classname", required=False, type=str, help="If the callable is a class function, specify the class name"
    )
    parser.add_argument(
        "--classparams",
        required=False,
        type=str,
        help="If the callable is a class function, specify the class constructor parameters (as a JSON string)",
    )
    parser.add_argument("--params", type=str, help="The parameters for the callable (as a JSON string)")
    args = parser.parse_args(explicit_args)
    return args


def resolve_callable(arguments: Namespace) -> Any:
    """Resolve the callable from the parsed arguments.

    Args:
      arguments (Namespace): The parsed command line arguments
    Returns:
      Any: The resolved callable (function or class method)

    """
    result = None

    if arguments.classname:
        _class = getattr(import_module(arguments.module), arguments.classname)
        class_instance = None
        if arguments.classparams:
            class_params: dict = json.loads(arguments.classparams)
            class_instance = _class(**class_params)
        else:
            class_instance = _class()
        result = getattr(class_instance, arguments.callable)
    else:
        result = getattr(import_module(arguments.module), arguments.callable)

    return result


def entrypoint(explicit_args: Sequence[str] | None = None) -> Any:
    """Execute a python callable based on command line arguments.

    Args:
      explicit_args: A sequence of command line arguments
    Returns:
      Any: The result of the executed callable

    """
    args: Namespace = parse_arguments(explicit_args)
    call = resolve_callable(args)
    if args.params:
        params: dict = json.loads(args.params)
        result: Any = call(**params)
    else:
        result: Any = call()
    # Print result to stdout for shell capture
    if result is not None:
        print(result)  # noqa: T201
    return result
