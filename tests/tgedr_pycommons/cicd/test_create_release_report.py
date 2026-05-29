"""Unit tests for create_release_report module."""
from unittest.mock import MagicMock, call, patch

import pytest
from fpdf import XPos, YPos

from tgedr_pycommons.cicd.create_release_report import (
    BLACK,
    BLUE,
    GREEN,
    add_section,
    generate_report,
    main,
    split_section,
)


def test_split_section_basic():  # noqa: ANN201, D103
    header, text = split_section("My Header\nLine one\nLine two")
    assert header == "My Header"
    assert text == "Line one\nLine two"


def test_split_section_no_body():  # noqa: ANN201, D103
    header, text = split_section("Only Header")
    assert header == "Only Header"
    assert text == ""


def test_add_section_defaults():  # noqa: ANN201, D103
    pdf = MagicMock()
    add_section(pdf, "Title\nSome body text")
    pdf.set_text_color.assert_any_call(*BLUE)
    pdf.set_font.assert_any_call("Helvetica", "B", 16)
    pdf.cell.assert_called_once_with(0, 10, "Title", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color.assert_any_call(*BLACK)
    pdf.set_font.assert_any_call("Helvetica", "", 12)
    pdf.multi_cell.assert_called_once_with(0, 8, "Some body text")


def test_add_section_custom_sizes_and_font():  # noqa: ANN201, D103
    pdf = MagicMock()
    add_section(pdf, "H\nbody", header_size=20, text_size=10, font="Courier")
    pdf.set_font.assert_any_call("Courier", "B", 20)
    pdf.set_font.assert_any_call("Courier", "", 10)


def test_generate_report(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "report.md"
    md.write_text(
        "preamble\n## Release 1.0\nIntro text\n## Tests\nAll good\n",
        encoding="utf-8",
    )
    output = str(tmp_path / "report.pdf")

    with patch("tgedr_pycommons.cicd.create_release_report.FPDF") as mock_fpdf_cls:
        mock_pdf = MagicMock()
        mock_fpdf_cls.return_value = mock_pdf
        generate_report(str(md), output)

    mock_pdf.add_page.assert_called_once()
    mock_pdf.output.assert_called_once_with(output)
    # ln(5) is called after title and after each subsequent section
    assert mock_pdf.ln.call_count == 2


def test_generate_report_multiple_sections(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "report.md"
    md.write_text(
        "## Title\ntitle body\n## Section A\nbody A\n## Section B\nbody B\n",
        encoding="utf-8",
    )
    output = str(tmp_path / "report.pdf")

    with patch("tgedr_pycommons.cicd.create_release_report.FPDF") as mock_fpdf_cls:
        mock_pdf = MagicMock()
        mock_fpdf_cls.return_value = mock_pdf
        generate_report(str(md), output)

    # green status cell called once per non-title section (2 sections)
    green_calls = [c for c in mock_pdf.set_text_color.call_args_list if c == call(*GREEN)]
    assert len(green_calls) == 2
    status_cells = [
        c for c in mock_pdf.cell.call_args_list
        if c == call(0, 10, "All tests passed!", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    ]
    assert len(status_cells) == 2


def test_main(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "report.md"
    md.write_text("## Title\nbody\n", encoding="utf-8")
    output = str(tmp_path / "out.pdf")

    with patch("sys.argv", ["prog", "--report", str(md), "--output", output]):
        with patch("tgedr_pycommons.cicd.create_release_report.generate_report") as mock_gen:
            main()

    mock_gen.assert_called_once_with(str(md), output)
