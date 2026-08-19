"""
QuestionParser: Uses NaturalPatternMatcher to identify question boundaries 
and builds the AST model (ExamRegion, ExamItem, ClusterBlock, QuestionBlock).
"""
import re
from typing import List, Optional, Tuple
from src.models.exam_structure import (
    XmlContentBlock,
    QuestionBlock,
    ClusterBlock,
    ExamItem,
    ExamRegion,
    ClusterMarkerType
)
from src.parsers.cluster_parser import RawClusterSegment

class QuestionParser:
    """
    Parses raw cluster segments into domain model objects.
    Uses pattern matching strictly for question boundaries (e.g., 'Câu 1.').
    """

    def __init__(self, pattern_matcher=None):
        self.pattern_matcher = pattern_matcher

    def _is_question_start(self, text: str) -> Optional[str]:
        """
        Extracts question number prefix if the text marks a question start.
        """
        text_clean = text.strip()
        if self.pattern_matcher and hasattr(self.pattern_matcher, "match_question_start"):
            match = self.pattern_matcher.match_question_start(text_clean)
            if match:
                return match

        # Regex fallback for standard natural question starts (Câu 1., Question 2:, Bài 3., 1., etc.)
        pattern = re.compile(r'^(Câu|Question|Bài|\d+)\s*(\d+)?\s*[\.\:\)\/]', re.IGNORECASE)
        m = pattern.match(text_clean)
        if m:
            return m.group(0)
        return None

    def _extract_text(self, block: XmlContentBlock) -> str:
        """Helper to extract visible text from XML string."""
        raw = block.raw_xml if block.raw_xml else ""
        # Simple extraction of text inside <w:t> tags
        texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', raw)
        return "".join(texts)

    def _parse_segment_questions(self, blocks: List[XmlContentBlock]) -> Tuple[List[XmlContentBlock], List[QuestionBlock]]:
        """
        Splits a list of blocks into (prefix_xml_blocks, questions).
        """
        prefix_blocks: List[XmlContentBlock] = []
        questions: List[QuestionBlock] = []
        
        current_q_num: Optional[str] = None
        current_q_blocks: List[XmlContentBlock] = []
        first_q_found = False

        for block in blocks:
            text = self._extract_text(block)
            q_num = self._is_question_start(text)

            if q_num:
                first_q_found = True
                if current_q_num or current_q_blocks:
                    # Flush current accumulated question
                    questions.append(QuestionBlock(
                        question_number=current_q_num,
                        xml_blocks=current_q_blocks
                    ))
                    current_q_blocks = []
                current_q_num = q_num
                current_q_blocks.append(block)
            else:
                if not first_q_found:
                    prefix_blocks.append(block)
                else:
                    current_q_blocks.append(block)

        if current_q_blocks:
            questions.append(QuestionBlock(
                question_number=current_q_num,
                xml_blocks=current_q_blocks
            ))

        return prefix_blocks, questions

    def parse_exam_region(
        self,
        pre_blocks: List[XmlContentBlock],
        raw_segments: List[RawClusterSegment],
        post_blocks: List[XmlContentBlock]
    ) -> ExamRegion:
        """
        Builds a complete ExamRegion from pre_blocks, raw_segments, and post_blocks.
        """
        exam_items: List[ExamItem] = []
        global_pos = 0

        for segment in raw_segments:
            prefix_blocks, questions = self._parse_segment_questions(segment.blocks)

            if segment.marker_type == ClusterMarkerType.NONE:
                # Normal questions outside any cluster marker
                for q in questions:
                    exam_items.append(ExamItem(
                        item_type="NORMAL",
                        question=q,
                        original_position=global_pos
                    ))
                    global_pos += 1
            else:
                # Cluster Block
                cluster = ClusterBlock(
                    marker_type=segment.marker_type,
                    prefix_xml_blocks=prefix_blocks,
                    questions=questions,
                    original_position=global_pos
                )
                exam_items.append(ExamItem(
                    item_type="CLUSTER",
                    cluster=cluster,
                    original_position=global_pos
                ))
                global_pos += 1

        return ExamRegion(
            pre_region_blocks=pre_blocks,
            exam_items=exam_items,
            post_region_blocks=post_blocks
        )
