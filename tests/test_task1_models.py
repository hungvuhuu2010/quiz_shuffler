"""
Unit tests for Task 1: Data Models & Exceptions.
"""
import pytest
from src.models.exam_structure import (
    ClusterMarkerType,
    XmlContentBlock,
    QuestionBlock,
    ClusterBlock,
    ExamItem,
    ExamRegion,
    TYPE_START_MARKER,
    TYPE_END_MARKER,
    CLUSTER_MARKERS
)
from src.models.exceptions import (
    QuizShufflerStructureError,
    MissingStartMarkerError,
    MissingEndMarkerError,
    InvalidClusterMarkerError,
    EmptyClusterError
)

def test_cluster_marker_types():
    assert ClusterMarkerType.NONE.value == "NONE"
    assert ClusterMarkerType.FIXED_ALL.value == "<##>"
    assert ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS.value == "<#?>"
    assert ClusterMarkerType.SHUFFLE_ALL.value == "<??>"

def test_xml_content_block():
    dummy_element = "ELEMENT_OBJ"
    raw = "<w:p><w:r><w:t>Sample</w:t></w:r></w:p>"
    block = XmlContentBlock(element=dummy_element, raw_xml=raw)
    assert block.element == dummy_element
    assert block.raw_xml == raw

def test_question_block_basic():
    q = QuestionBlock(question_number="Câu 1", xml_blocks=[])
    assert q.question_number == "Câu 1"
    assert q.xml_blocks == []

def test_question_block_multiple_xml():
    b1 = XmlContentBlock(element=None, raw_xml="<w:p>Câu 1</w:p>")
    b2 = XmlContentBlock(element=None, raw_xml="<w:tbl>Table</w:tbl>")
    b3 = XmlContentBlock(element=None, raw_xml="<w:p>A. Choice</w:p>")
    q = QuestionBlock(question_number="1", xml_blocks=[b1, b2, b3])
    assert len(q.xml_blocks) == 3
    assert q.xml_blocks[1].raw_xml == "<w:tbl>Table</w:tbl>"

def test_cluster_block_fixed_all():
    cb = ClusterBlock(marker_type=ClusterMarkerType.FIXED_ALL, original_position=1)
    assert cb.marker_type == ClusterMarkerType.FIXED_ALL
    assert cb.original_position == 1

def test_cluster_block_fixed_pos_shuffle_questions():
    cb = ClusterBlock(marker_type=ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS, original_position=2)
    assert cb.marker_type == ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS

def test_cluster_block_shuffle_all():
    cb = ClusterBlock(marker_type=ClusterMarkerType.SHUFFLE_ALL, original_position=3)
    assert cb.marker_type == ClusterMarkerType.SHUFFLE_ALL

def test_cluster_block_with_prefix():
    prefix_block = XmlContentBlock(element=None, raw_xml="<w:p>Passage text</w:p>")
    q_block = QuestionBlock(question_number="Câu 1", xml_blocks=[])
    cb = ClusterBlock(
        marker_type=ClusterMarkerType.FIXED_ALL,
        prefix_xml_blocks=[prefix_block],
        questions=[q_block],
        original_position=0
    )
    assert len(cb.prefix_xml_blocks) == 1
    assert cb.prefix_xml_blocks[0].raw_xml == "<w:p>Passage text</w:p>"
    assert len(cb.questions) == 1

def test_cluster_block_no_prefix():
    cb = ClusterBlock(marker_type=ClusterMarkerType.FIXED_ALL, prefix_xml_blocks=[])
    assert cb.prefix_xml_blocks == []

def test_exam_item_normal():
    q = QuestionBlock(question_number="Câu 1", xml_blocks=[])
    item = ExamItem(item_type="NORMAL", question=q, original_position=0)
    assert item.is_normal_question() is True
    assert item.is_cluster() is False
    assert item.question.question_number == "Câu 1"

def test_exam_item_cluster():
    cb = ClusterBlock(marker_type=ClusterMarkerType.SHUFFLE_ALL, original_position=1)
    item = ExamItem(item_type="CLUSTER", cluster=cb, original_position=1)
    assert item.is_cluster() is True
    assert item.is_normal_question() is False
    assert item.cluster.marker_type == ClusterMarkerType.SHUFFLE_ALL

def test_exam_region_structure():
    pre = [XmlContentBlock(element=None, raw_xml="<w:p>Title</w:p>")]
    post = [XmlContentBlock(element=None, raw_xml="<w:p>End</w:p>")]
    q = QuestionBlock(question_number="Câu 1", xml_blocks=[])
    item = ExamItem(item_type="NORMAL", question=q)
    
    region = ExamRegion(
        pre_region_blocks=pre,
        exam_items=[item],
        post_region_blocks=post
    )
    assert len(region.pre_region_blocks) == 1
    assert len(region.exam_items) == 1
    assert len(region.post_region_blocks) == 1

def test_exception_hierarchy():
    assert issubclass(MissingStartMarkerError, QuizShufflerStructureError)
    assert issubclass(MissingEndMarkerError, QuizShufflerStructureError)
    assert issubclass(InvalidClusterMarkerError, QuizShufflerStructureError)
    assert issubclass(EmptyClusterError, QuizShufflerStructureError)

def test_missing_end_marker_error():
    with pytest.raises(MissingEndMarkerError) as exc_info:
        raise MissingEndMarkerError()
    assert "<end 1>" in str(exc_info.value)

def test_missing_start_marker_error():
    with pytest.raises(MissingStartMarkerError) as exc_info:
        raise MissingStartMarkerError()
    assert "<type 1>" in str(exc_info.value)

def test_invalid_cluster_marker_error():
    with pytest.raises(InvalidClusterMarkerError) as exc_info:
        raise InvalidClusterMarkerError("<###>")
    assert "<###>" in str(exc_info.value)

def test_empty_cluster_error():
    with pytest.raises(EmptyClusterError) as exc_info:
        raise EmptyClusterError("<##>")
    assert "<##>" in str(exc_info.value)
