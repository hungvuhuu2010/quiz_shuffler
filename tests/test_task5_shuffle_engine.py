"""
Unit tests for Task 5: ShuffleEngine
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
from src.engine.shuffle_engine import ShuffleEngine

def make_q(num: str) -> QuestionBlock:
    return QuestionBlock(question_number=f"Câu {num}", xml_blocks=[])

def make_normal_item(num: str, pos: int) -> ExamItem:
    return ExamItem(item_type="NORMAL", question=make_q(num), original_position=pos)

def make_cluster_item(marker: ClusterMarkerType, q_nums: list, pos: int) -> ExamItem:
    cb = ClusterBlock(
        marker_type=marker,
        prefix_xml_blocks=[],
        questions=[make_q(n) for n in q_nums],
        original_position=pos
    )
    return ExamItem(item_type="CLUSTER", cluster=cb, original_position=pos)

def test_fixed_all_cluster_never_moves_or_shuffles():
    # Fixed seed for deterministic testing
    engine = ShuffleEngine(seed=42)
    c1 = make_cluster_item(ClusterMarkerType.FIXED_ALL, ["1", "2", "3"], 0)
    region = ExamRegion(pre_region_blocks=[], exam_items=[c1], post_region_blocks=[])
    
    shuffled = engine.shuffle_exam_region(region)
    cluster = shuffled.exam_items[0].cluster

    assert cluster.marker_type == ClusterMarkerType.FIXED_ALL
    q_numbers = [q.question_number for q in cluster.questions]
    assert q_numbers == ["Câu 1", "Câu 2", "Câu 3"]

def test_fixed_pos_shuffle_questions_cluster_position_fixed_questions_shuffled():
    # Use seed where 3 elements will change order
    engine = ShuffleEngine(seed=123)
    c_fixed = make_cluster_item(ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS, ["10", "20", "30", "40"], 0)
    region = ExamRegion(pre_region_blocks=[], exam_items=[c_fixed], post_region_blocks=[])

    shuffled = engine.shuffle_exam_region(region)
    cluster = shuffled.exam_items[0].cluster

    q_numbers = [q.question_number for q in cluster.questions]
    # Position fixed, but order shuffled
    assert sorted(q_numbers) == ["Câu 10", "Câu 20", "Câu 30", "Câu 40"]
    assert q_numbers != ["Câu 10", "Câu 20", "Câu 30", "Câu 40"]

def test_shuffle_all_and_normal_questions_interleaved():
    engine = ShuffleEngine(seed=99)
    q1 = make_normal_item("1", 0)
    c_fixed = make_cluster_item(ClusterMarkerType.FIXED_ALL, ["2", "3"], 1)
    q4 = make_normal_item("4", 2)
    c_shuffle = make_cluster_item(ClusterMarkerType.SHUFFLE_ALL, ["5", "6"], 3)

    region = ExamRegion(pre_region_blocks=[], exam_items=[q1, c_fixed, q4, c_shuffle], post_region_blocks=[])
    shuffled = engine.shuffle_exam_region(region)

    # Index 1 MUST remain the fixed cluster
    assert shuffled.exam_items[1].is_cluster()
    assert shuffled.exam_items[1].cluster.marker_type == ClusterMarkerType.FIXED_ALL
    assert [q.question_number for q in shuffled.exam_items[1].cluster.questions] == ["Câu 2", "Câu 3"]
