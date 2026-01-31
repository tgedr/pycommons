from tgedr.pycommons.data.processing import process_text_array


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
