"""
ShuffleEngine: Applies strict shuffling rules to ExamRegion components 
based on ClusterMarkerType specifications.
"""
import random
import copy
from typing import List, Optional
from src.models.exam_structure import (
    ExamRegion,
    ExamItem,
    ClusterBlock,
    QuestionBlock,
    ClusterMarkerType
)

class ShuffleEngine:
    """
    Executes shuffling on an ExamRegion while strictly respecting marker contracts:
    - FIXED_ALL (<##>): Position fixed, question order fixed.
    - FIXED_POS_SHUFFLE_QUESTIONS (<#?>): Position fixed, inner questions shuffled.
    - SHUFFLE_ALL (<??>): Position shuffled with movable items, inner questions shuffled.
    - NORMAL: Position shuffled with movable items.
    """

    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)

    def shuffle_exam_region(self, region: ExamRegion) -> ExamRegion:
        """
        Returns a new ExamRegion with shuffled items and inner questions based on rules.
        """
        # Deep copy to avoid mutating original structure
        shuffled_items = copy.deepcopy(region.exam_items)

        # Step 1: Shuffle questions inside clusters that allow question shuffling (<#?> and <??>)
        for item in shuffled_items:
            if item.is_cluster():
                cluster = item.cluster
                if cluster.marker_type in (
                    ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS,
                    ClusterMarkerType.SHUFFLE_ALL
                ):
                    if len(cluster.questions) > 1:
                        self.random.shuffle(cluster.questions)

        # Step 2: Separate items into fixed-position slots vs movable items
        total_len = len(shuffled_items)
        result_items: List[Optional[ExamItem]] = [None] * total_len

        movable_indices: List[int] = []
        movable_items: List[ExamItem] = []

        for idx, item in enumerate(shuffled_items):
            if item.is_cluster() and item.cluster.marker_type in (
                ClusterMarkerType.FIXED_ALL,
                ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS
            ):
                # Fixed position in exam region
                result_items[idx] = item
            else:
                # Movable item (NORMAL questions or <??> clusters)
                movable_indices.append(idx)
                movable_items.append(item)

        # Step 3: Shuffle movable items and place back into movable slots
        if len(movable_items) > 1:
            self.random.shuffle(movable_items)

        for slot_idx, item in zip(movable_indices, movable_items):
            result_items[slot_idx] = item

        return ExamRegion(
            pre_region_blocks=copy.deepcopy(region.pre_region_blocks),
            exam_items=[item for item in result_items if item is not None],
            post_region_blocks=copy.deepcopy(region.post_region_blocks)
        )
