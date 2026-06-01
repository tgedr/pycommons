"""Unit tests for markdown_to_pdf module."""

from unittest.mock import patch

import pytest

from tgedr_pycommons.cicd.markdown_to_pdf import _split_html_blocks, convert


def test_convert_creates_pdf(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "input.md"
    md.write_text("# Hello\n\nThis is a test.", encoding="utf-8")
    output = str(tmp_path / "output.pdf")

    convert(str(md), output)

    assert (tmp_path / "output.pdf").exists()
    assert (tmp_path / "output.pdf").stat().st_size > 0


def test_convert_file_not_found():  # noqa: ANN201, D103
    with pytest.raises(FileNotFoundError):
        convert("nonexistent.md", "output.pdf")


def test_convert_handles_unicode(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "unicode.md"
    md.write_text("# Héllo wörld\n\nEmojis: 🎉 and accents: café", encoding="utf-8")
    output = str(tmp_path / "output.pdf")

    convert(str(md), output)

    assert (tmp_path / "output.pdf").exists()


def test_convert_empty_file(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "empty.md"
    md.write_text("", encoding="utf-8")
    output = str(tmp_path / "output.pdf")

    convert(str(md), output)

    assert (tmp_path / "output.pdf").exists()


def test_convert_full_document(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "full.md"
    md.write_text(
        "# Title\n\nIntro **bold** and *italic*.\n\n## Section\n\n- bullet\n- another\n\n"
        "```python\ndef hello():\n    pass\n```\n\n---\n\n1. one\n2. two\n",
        encoding="utf-8",
    )
    output = str(tmp_path / "output.pdf")

    convert(str(md), output)

    assert (tmp_path / "output.pdf").exists()


def test_convert_skips_empty_blocks(tmp_path):  # noqa: ANN201, D103
    md = tmp_path / "input.md"
    md.write_text("# Hello", encoding="utf-8")
    output = str(tmp_path / "output.pdf")

    with patch("tgedr_pycommons.cicd.markdown_to_pdf._split_html_blocks", return_value=["", "  ", "<h1>Hello</h1>"]):
        convert(str(md), output)

    assert (tmp_path / "output.pdf").exists()


def test_split_html_blocks_single_block():  # noqa: ANN201, D103
    result = _split_html_blocks("<p>hello</p>")
    assert result == ["<p>hello</p>"]


def test_split_html_blocks_multiple():  # noqa: ANN201, D103
    result = _split_html_blocks("<h1>Title</h1>\n<p>body</p>")
    assert result == ["<h1>Title</h1>", "<p>body</p>"]


def test_split_html_blocks_multiline_block():  # noqa: ANN201, D103
    result = _split_html_blocks("<ul>\n<li>one</li>\n<li>two</li>\n</ul>")
    assert result == ["<ul>", "<li>one</li>", "<li>two</li>", "</ul>"]
