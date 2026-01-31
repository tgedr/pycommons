"""Utilities for processing data."""

from typing import Any, Callable  # noqa: UP035
import numpy as np


def process_text_array(x: list, f: Callable[[str], Any]) -> list:
    """Apply a transformation function to each string in a nested text array.

    Parameters
    ----------
    x : list
        A (possibly nested) list of strings that should form a balanced array.
    f : Callable[[str], Any]
        A function applied to each string element.

    Returns
    -------
    list
        A nested list with the same structure as `x` containing transformed items.

    Raises
    ------
    ValueError
        If `x` cannot be converted to a balanced NumPy array.

    """
    try:
        np.array(x)
    except ValueError as e:
        msg = f"x must be a balanced array, convertible to a numpy array. Error: {e}"
        raise ValueError(msg) from e

    def unidim_process(x: list, f: Callable[[str], Any]) -> list:
        result = []
        for t in x:
            output = f(t)
            result.append(output)
        return result

    def multidim_process(x: list, f: Callable[[str], Any]) -> list:
        result = []
        if 1 == np.array(x).ndim:  # noqa: SIM300
            result = unidim_process(x=x, f=f)
        else:
            for s in x:
                result.append(multidim_process(x=s, f=f))
        return result

    return multidim_process(x=x, f=f)
