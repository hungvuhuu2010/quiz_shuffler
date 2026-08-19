"""
Unit tests for Task 6: DocxWriter & Marker Stripper
"""
import pytest
from src.models.exam_structure import (
    XmlContentBlock,
    QuestionBlock,
    ClusterBlock,
    ExamItem,
    ExamRegion,
    ClusterMarkerType
)
from src.writers.docx_writer import DocxWriter

def make_block(text: str) -> XmlContentBlock:
    raw_xml = f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
    return XmlContentBlock(element=None, raw_xml=raw_xml)

def test_marker_only_block_is_removed():
    writer = DocxWriter()
    marker_block = make_block("<##>")
    result = writer.process_block(marker_block)
    assert len(result) == 0

def test_inline_marker_is_stripped_content_preserved():
    writer = DocxWriter()
    inline_block = make_block("<type 1> Đề thi Học kỳ I")
    result = writer.process_block(inline_block)
    assert len(result) == 1
    assert "<type 1>" not in result[0].raw_xml
    assert "Đề thi Học kỳ I" in result[0].raw_xml

def test_build_final_xml_blocks_removes_all_control_markers():
    writer = DocxWriter()
    pre = [make_block("Header text"), make_block("<type 1>")]
    
    q1 = QuestionBlock(question_number="1", xml_blocks=[make_block("Câu 1. Nội dung 1")])
    item_q1 = ExamItem(item_type="NORMAL", question=q1)
    
    c_prefix = [make_block("<#?>"), make_block("Đoạn văn dẫn chung")]
    c_q2 = QuestionBlock(question_number="2", xml_blocks=[make_block("Câu 2. Nội dung 2")])
    cluster = ClusterBlock(
        marker_type=ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS,
        prefix_xml_blocks=c_prefix,
        questions=[c_q2]
    )
    item_cluster = ExamItem(item_type="CLUSTER", cluster=cluster)

    post = [make_block("<end 1>"), make_block("Footer text")]

    region = ExamRegion(
        pre_region_blocks=pre,
        exam_items=[item_q1, item_cluster],
        post_region_blocks=post
    )

    final_blocks = writer.build_final_xml_blocks(region)
    final_texts = [b.raw_xml for b in final_blocks]

    # Verify control markers are completely gone
    for text in final_texts:
        assert "<type 1>" not in text
        assert "<end 1>" not in text
        assert "<#?>" not in text

    # Verify content preserved
    combined = "".join(final_texts)
    assert "Header text" in combined
    assert "Câu 1. Nội dung 1" in combined
    assert "Đoạn văn dẫn chung" in combined
    assert "Câu 2. Nội dung 2" in combined
    assert "Footer text" in combined
