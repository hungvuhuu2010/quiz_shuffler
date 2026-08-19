"""
Domain models for Quiz Shuffler structure.
"""
from enum import Enum
from typing import List, Optional, Any
from dataclasses import dataclass, field

# Constants
TYPE_START_MARKER = "<type 1>"
TYPE_END_MARKER = "<end 1>"

CLUSTER_MARKERS = {
    "<##>",
    "<#?>",
    "<??>"
}

class ClusterMarkerType(Enum):
    NONE = "NONE"
    FIXED_ALL = "<##>"
    FIXED_POS_SHUFFLE_QUESTIONS = "<#?>"
    SHUFFLE_ALL = "<??>"

@dataclass
class XmlContentBlock:
    """Represents a single raw XML node (Paragraph or Table) from DOCX."""
    element: Any
    raw_xml: str

@dataclass
class QuestionBlock:
    """Represents a single question containing all its constituent XML blocks."""
    question_number: Optional[str]
    xml_blocks: List[XmlContentBlock] = field(default_factory=list)

@dataclass
class ClusterBlock:
    """Represents a cluster/group of questions defined strictly by cluster markers."""
    marker_type: ClusterMarkerType
    prefix_xml_blocks: List[XmlContentBlock] = field(default_factory=list)
    questions: List[QuestionBlock] = field(default_factory=list)
    original_position: int = 0

@dataclass
class ExamItem:
    """
    Polymorphic container for items inside an ExamRegion.
    Can either wrap a single QuestionBlock (NORMAL) or a ClusterBlock (CLUSTER).
    """
    item_type: str  # "NORMAL" or "CLUSTER"
    question: Optional[QuestionBlock] = None
    cluster: Optional[ClusterBlock] = None
    original_position: int = 0

    def is_cluster(self) -> bool:
        return self.item_type == "CLUSTER" and self.cluster is not None

    def is_normal_question(self) -> bool:
        return self.item_type == "NORMAL" and self.question is not None

@dataclass
class ExamRegion:
    """Represents the processing region bounds defined by <type 1> and <end 1>."""
    pre_region_blocks: List[XmlContentBlock] = field(default_factory=list)
    exam_items: List[ExamItem] = field(default_factory=list)
    post_region_blocks: List[XmlContentBlock] = field(default_factory=list)
