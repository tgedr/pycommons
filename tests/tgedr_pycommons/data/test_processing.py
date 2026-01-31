import pytest
from tgedr_pycommons.data.processing import process_text_array


def test_process_text_array():
    SEQUENCE_MAX_LEN = 10
    x = [
      [
        ['Apple', 'looking'],
        ['Autonomous', 'cars']
      ],
      [
        ['The', 'Pope'],
        ['Mary', 'was']
      ]
    ]
    expected = [
      [
          ['APPLE', 'LOOKING' ],
          ['AUTONOMOUS', 'CARS']
        ],
        [
          ['THE', 'POPE'], 
          ['MARY', 'WAS']
        ]
      ]
    actual = process_text_array(x=x, f=lambda s: s.upper())
    assert actual == expected


def test_process_text_array_unbalanced():
    """Test that unbalanced arrays raise ValueError."""
    # Unbalanced array - different lengths in nested lists
    x = [
        ['Apple', 'looking', 'extra'],
        ['Autonomous', 'cars']
    ]
    
    with pytest.raises(ValueError, match="x must be a balanced array"):
        process_text_array(x=x, f=lambda s: s.upper())
