"""
Unit tests for Task 4: QuestionParser
"""
import pytest
from src.models.exam_structure import XmlContentBlock, ClusterMarkerType
from src.parsers.cluster_parser import RawClusterSegment
from src.parsers.question_parser import QuestionParser

def make_block(text: str) -> XmlContentBlock:
    raw_xml = f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
    return XmlContentBlock(element=None, raw_xml=raw_xml)

def test_parse_normal_questions():
    parser = QuestionParser()
    blocks = [
        make_block("Câu 1. Hỏi điều A?"),
        make_block("A. Đáp án A"),
        make_block("Câu 2. Hỏi điều B?"),
        make_block("B. Đáp án B")
    ]
    segment = RawClusterSegment(
        marker_type=ClusterMarkerType.NONE,
        blocks=blocks,
        original_position=0
    )
    
    region = parser.parse_exam_region([], [segment], [])
    assert len(region.exam_items) == 2
    assert region.exam_items[0].is_normal_question()
    assert region.exam_items[0].question.question_number.startswith("Câu 1")
    assert len(region.exam_items[0].question.xml_blocks) == 2

    assert region.exam_items[1].is_normal_question()
    assert region.exam_items[1].question.question_number.startswith("Câu 2")

def test_parse_cluster_with_prefix():
    parser = QuestionParser()
    blocks = [
        make_block("<##>"),
        make_block("Dựa vào văn bản sau để trả lời..."),
        make_block("Câu 3. Hỏi..."),
        make_block("Câu 4. Hỏi...")
    ]
    segment = RawClusterSegment(
        marker_type=ClusterMarkerType.FIXED_ALL,
        blocks=blocks,
        original_position=0
    )

    region = parser.parse_exam_region([], [segment], [])
    assert len(region.exam_items) == 1
    item = region.exam_items[0]
    assert item.is_cluster()
    assert item.cluster.marker_type == ClusterMarkerType.FIXED_ALL
    assert len(item.cluster.prefix_xml_blocks) == 2
    assert len(item.cluster.questions) == 2

def test_parse_interleaved_normal_and_clusters():
    parser = QuestionParser()
    seg1 = RawClusterSegment(
        marker_type=ClusterMarkerType.NONE,
        blocks=[make_block("Câu 1. Bình thường")],
        original_position=0
    )
    seg2 = RawClusterSegment(
        marker_type=ClusterMarkerType.SHUFFLE_ALL,
        blocks=[make_block("<??>"), make_block("Câu 2. Trong chùm 1"), make_block("Câu 3. Trong chùm 1")],
        original_position=1
    )
    seg3 = RawClusterSegment(
        marker_type=ClusterMarkerType.NONE,
        blocks=[make_block("Câu 4. Bình thường")],
        original_position=2
    )

    region = parser.parse_exam_region([], [seg1, seg2, seg3], [])
    assert len(region.exam_items) == 3
    assert region.exam_items[0].is_normal_question()
    assert region.exam_items[1].is_cluster()
    assert len(region.exam_items[1].cluster.questions) == 2
    assert region.exam_items[2].is_normal_question()
