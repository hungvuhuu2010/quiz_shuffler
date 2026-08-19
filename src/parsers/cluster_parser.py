"""
ClusterMarkerParser: Parses raw XML blocks in the exam region into 
cluster raw segments based strictly on cluster markers (<##>, <#?>, <??>).
"""
import re
from typing import List, Dict, Any, Tuple
from src.models.exam_structure import (
    XmlContentBlock,
    ClusterMarkerType,
    CLUSTER_MARKERS
)
from src.models.exceptions import (
    InvalidClusterMarkerError,
    EmptyClusterError
)

# Pattern to detect potential marker tokens like <##>, <#?>, <??>, <###>, etc.
POTENTIAL_MARKER_PATTERN = re.compile(r"<[#?]{1,3}>")

MARKER_MAP = {
    "<##>": ClusterMarkerType.FIXED_ALL,
    "<#?>": ClusterMarkerType.FIXED_POS_SHUFFLE_QUESTIONS,
    "<??>": ClusterMarkerType.SHUFFLE_ALL
}

class RawClusterSegment:
    """Represents an unparsed raw segment tagged with a cluster marker."""
    def __init__(self, marker_type: ClusterMarkerType, blocks: List[XmlContentBlock], original_position: int):
        self.marker_type = marker_type
        self.blocks = blocks
        self.original_position = original_position

class ClusterMarkerParser:
    """
    Parses exam region XML blocks into raw cluster segments based strictly on markers.
    Does NOT attempt semantic guessing.
    """

    def parse_cluster_segments(self, exam_blocks: List[XmlContentBlock]) -> List[RawClusterSegment]:
        """
        Splits exam_blocks into RawClusterSegments based on cluster markers.
        Blocks occurring before the first cluster marker are assigned ClusterMarkerType.NONE.

        Raises:
            InvalidClusterMarkerError: If an invalid syntax like <###> is detected.
            EmptyClusterError: If a cluster marker contains no subsequent blocks.
        """
        segments: List[RawClusterSegment] = []
        current_marker_type = ClusterMarkerType.NONE
        current_blocks: List[XmlContentBlock] = []
        current_position = 0

        for block in exam_blocks:
            raw = block.raw_xml if block.raw_xml else ""

            # Check for invalid marker syntaxes
            found_tokens = POTENTIAL_MARKER_PATTERN.findall(raw)
            for token in found_tokens:
                if token not in CLUSTER_MARKERS and token not in ("<type 1>", "<end 1>"):
                    raise InvalidClusterMarkerError(token)

            # Check for valid cluster markers
            detected_marker = None
            for marker_str in CLUSTER_MARKERS:
                if marker_str in raw:
                    detected_marker = marker_str
                    break

            if detected_marker:
                # Flush existing accumulated blocks as a segment
                if current_blocks:
                    segments.append(RawClusterSegment(
                        marker_type=current_marker_type,
                        blocks=current_blocks,
                        original_position=current_position
                    ))
                    current_position += 1
                    current_blocks = []
                elif current_marker_type != ClusterMarkerType.NONE:
                    # Previous cluster marker had no blocks before next marker appeared
                    raise EmptyClusterError(current_marker_type.value)

                current_marker_type = MARKER_MAP[detected_marker]
                current_blocks.append(block)
            else:
                current_blocks.append(block)

        # Flush final remaining segment
        if current_blocks:
            # If the last block was just a marker without any question content following it
            if current_marker_type != ClusterMarkerType.NONE and len(current_blocks) == 1:
                first_raw = current_blocks[0].raw_xml
                # If only the marker is in the block, raise EmptyClusterError
                if any(m in first_raw for m in CLUSTER_MARKERS) and len(first_raw.strip()) < 50:
                    raise EmptyClusterError(current_marker_type.value)

            segments.append(RawClusterSegment(
                marker_type=current_marker_type,
                blocks=current_blocks,
                original_position=current_position
            ))
        elif current_marker_type != ClusterMarkerType.NONE:
            raise EmptyClusterError(current_marker_type.value)

        return segments
