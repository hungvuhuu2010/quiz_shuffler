"""
QuestionRegionDetector: Identifies and extracts the processing bounds 
defined by <type 1> and <end 1> markers.
"""
from typing import List, Tuple
from src.models.exam_structure import (
    XmlContentBlock,
    TYPE_START_MARKER,
    TYPE_END_MARKER
)
from src.models.exceptions import (
    MissingStartMarkerError,
    MissingEndMarkerError
)

class QuestionRegionDetector:
    """
    Scans XML content blocks to separate the document into:
    1. Pre-region blocks (before <type 1>)
    2. Exam blocks (between <type 1> and <end 1>)
    3. Post-region blocks (after <end 1>)
    """

    def detect_regions(
        self, blocks: List[XmlContentBlock]
    ) -> Tuple[List[XmlContentBlock], List[XmlContentBlock], List[XmlContentBlock]]:
        """
        Splits blocks into (pre_blocks, exam_blocks, post_blocks).

        Raises:
            MissingStartMarkerError: If <end 1> is found without <type 1>.
            MissingEndMarkerError: If <type 1> is found without <end 1>.
        """
        start_index = -1
        end_index = -1

        for idx, block in enumerate(blocks):
            # Check raw_xml for marker text
            raw = block.raw_xml if block.raw_xml else ""
            
            if TYPE_START_MARKER in raw:
                if start_index != -1:
                    # If multiple <type 1> markers exist, last or first depending on design,
                    # but here we record the first start marker encounter.
                    pass
                else:
                    start_index = idx

            if TYPE_END_MARKER in raw:
                end_index = idx
                # If <end 1> appears before <type 1>, it's invalid
                if start_index == -1:
                    raise MissingStartMarkerError()

        # Validation logic
        if start_index != -1 and end_index == -1:
            raise MissingEndMarkerError()

        # If no markers present at all -> treat entire doc as exam region
        if start_index == -1 and end_index == -1:
            return [], list(blocks), []

        pre_blocks = blocks[:start_index]
        exam_blocks = blocks[start_index:end_index + 1]
        post_blocks = blocks[end_index + 1:]

        return pre_blocks, exam_blocks, post_blocks
