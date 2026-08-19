"""
Unit tests for Task 2: QuestionRegionDetector
"""
import pytest
from src.models.exam_structure import XmlContentBlock
from src.models.exceptions import MissingStartMarkerError, MissingEndMarkerError
from src.parsers.region_detector import QuestionRegionDetector

def make_block(text: str) -> XmlContentBlock:
    raw_xml = f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
    return XmlContentBlock(element=None, raw_xml=raw_xml)

def test_no_markers_returns_all_as_exam():
    detector = QuestionRegionDetector()
    blocks = [make_block("Câu 1. Hỏi..."), make_block("Câu 2. Hỏi...")]
    pre, exam, post = detector.detect_regions(blocks)
    
    assert len(pre) == 0
    assert len(exam) == 2
    assert len(post) == 0

def test_valid_start_and_end_markers():
    detector = QuestionRegionDetector()
    blocks = [
        make_block("Tiêu đề đề thi"),
        make_block("<type 1>"),
        make_block("Câu 1. Hỏi..."),
        make_block("Câu 2. Hỏi..."),
        make_block("<end 1>"),
        make_block("Lời kết / Đáp án")
    ]
    pre, exam, post = detector.detect_regions(blocks)

    assert len(pre) == 1
    assert pre[0].raw_xml == "<w:p><w:r><w:t>Tiêu đề đề thi</w:t></w:r></w:p>"

    assert len(exam) == 4
    assert exam[0].raw_xml == "<w:p><w:r><w:t>&lt;type 1&gt;</w:t></w:r></w:p>".replace("&lt;type 1&gt;", "<type 1>")

    assert len(post) == 1
    assert "Lời kết" in post[0].raw_xml

def test_missing_end_marker_raises_error():
    detector = QuestionRegionDetector()
    blocks = [
        make_block("<type 1>"),
        make_block("Câu 1. Hỏi...")
    ]
    with pytest.raises(MissingEndMarkerError):
        detector.detect_regions(blocks)

def test_missing_start_marker_raises_error():
    detector = QuestionRegionDetector()
    blocks = [
        make_block("Câu 1. Hỏi..."),
        make_block("<end 1>")
    ]
    with pytest.raises(MissingStartMarkerError):
        detector.detect_regions(blocks)
