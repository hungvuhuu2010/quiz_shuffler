"""
Unit tests for Task 3: ClusterMarkerParser
"""
import pytest
from src.models.exam_structure import XmlContentBlock, ClusterMarkerType
from src.models.exceptions import InvalidClusterMarkerError, EmptyClusterError
from src.parsers.cluster_parser import ClusterMarkerParser

def make_block(text: str) -> XmlContentBlock:
    raw_xml = f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
    return XmlContentBlock(element=None, raw_xml=raw_xml)

def test_no_cluster_markers_returns_none_marker_type():
    parser = ClusterMarkerParser()
    blocks = [make_block("Câu 1. Hỏi..."), make_block("Câu 2. Hỏi...")]
    segments = parser.parse_cluster_segments(blocks)

    assert len(segments) == 1
    assert segments[0].marker_type == ClusterMarkerType.NONE
    assert len(segments[0].blocks) == 2

def test_single_fixed_all_cluster():
    parser = ClusterMarkerParser()
    blocks = [
        make_block("<##>"),
        make_block("Đoạn văn dẫn chung..."),
        make_block("Câu 1. Hỏi..."),
        make_block("Câu 2. Hỏi...")
    ]
    segments = parser.parse_cluster_segments(blocks)

    assert len(segments) == 1
    assert segments[0].marker_type == ClusterMarkerType.FIXED_ALL
    assert len(segments[0].blocks) == 4

def test_multiple_consecutive_clusters():
    parser = ClusterMarkerParser()
    blocks = [
        make_block("<##>"),
        make_block("Câu 1. Hỏi..."),
        make_block("<#?>"),
        make_block("Câu 2. Hỏi..."),
        make_block("<??>"),
        make_block("Câu 3. Hỏi...")
    ]
    segments = parser.parse_cluster_segments(blocks)

    assert len(segments) == 3
    assert segments[0].marker_type == ClusterMarkerType.FIXED_ALL
    assert segments[1].marker_type == ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS
    assert segments[2].marker_type == ClusterMarkerType.SHUFFLE_ALL

def test_invalid_cluster_marker_syntax_raises_error():
    parser = ClusterMarkerParser()
    blocks = [
        make_block("<###>"),
        make_block("Câu 1. Hỏi...")
    ]
    with pytest.raises(InvalidClusterMarkerError) as exc_info:
        parser.parse_cluster_segments(blocks)
    assert "<###>" in str(exc_info.value)

def test_empty_cluster_raises_error():
    parser = ClusterMarkerParser()
    blocks = [
        make_block("<##>")
    ]
    with pytest.raises(EmptyClusterError):
        parser.parse_cluster_segments(blocks)
