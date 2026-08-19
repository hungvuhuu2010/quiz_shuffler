"""
Unit & Integration tests for Step 3 CLI & File Adapter.
"""
import pytest
from pathlib import Path
from src.cli import build_parser, main
from src.file_adapter import DocxFileAdapter
from src.models.exam_structure import XmlContentBlock


def make_p(text: str) -> XmlContentBlock:
    raw = f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
    return XmlContentBlock(element=None, raw_xml=raw)


def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["-i", "test.docx"])
    assert args.input == "test.docx"
    assert args.num_versions == 1
    assert args.output_dir == "output"


def test_cli_parser_custom_options():
    parser = build_parser()
    args = parser.parse_args([
        "-i", "exam.docx",
        "-o", "out.docx",
        "-n", "4",
        "-s", "123"
    ])
    assert args.input == "exam.docx"
    assert args.output == "out.docx"
    assert args.num_versions == 4
    assert args.seed == 123


def test_docx_file_adapter_direct_block_processing():
    adapter = DocxFileAdapter(seed=42)
    raw_blocks = [
        make_p("<type 1>"),
        make_p("Câu 1. Hỏi..."),
        make_p("Câu 2. Hỏi..."),
        make_p("<end 1>")
    ]
    processed = adapter.process_docx_blocks(raw_blocks)
    combined = "".join([b.raw_xml for b in processed])

    assert "<type 1>" not in combined
    assert "Câu 1. Hỏi..." in combined
    assert "Câu 2. Hỏi..." in combined
