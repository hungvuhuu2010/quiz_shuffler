"""
QuizShufflerPipeline: Facade that wires together all core components 
for End-to-End DOCX exam shuffling.
"""
from typing import Optional, List
from src.models.exam_structure import XmlContentBlock, ExamRegion
from src.parsers.region_detector import QuestionRegionDetector
from src.parsers.cluster_parser import ClusterMarkerParser
from src.parsers.question_parser import QuestionParser
from src.engine.shuffle_engine import ShuffleEngine
from src.writers.docx_writer import DocxWriter


class QuizShufflerPipeline:
    """
    End-to-End pipeline executing the complete shuffle workflow:
    DocxXmlExtractor Blocks -> Region Detector -> Cluster Marker Parser 
    -> Question Parser -> Shuffle Engine -> DocxWriter -> Clean XmlContentBlocks
    """

    def __init__(self, seed: Optional[int] = None, pattern_matcher=None):
        self.region_detector = QuestionRegionDetector()
        self.cluster_parser = ClusterMarkerParser()
        self.question_parser = QuestionParser(pattern_matcher=pattern_matcher)
        self.shuffle_engine = ShuffleEngine(seed=seed)
        self.docx_writer = DocxWriter()

    def process_blocks(self, raw_blocks: List[XmlContentBlock]) -> List[XmlContentBlock]:
        """
        Processes a raw list of XmlContentBlocks and returns the final shuffled, cleaned blocks.
        """
        # 1. Detect processing regions (<type 1> ... <end 1>)
        pre_blocks, exam_blocks, post_blocks = self.region_detector.detect_regions(raw_blocks)

        # 2. Parse raw cluster segments by markers (<##>, <#?>, <??>)
        raw_segments = self.cluster_parser.parse_cluster_segments(exam_blocks)

        # 3. Parse boundaries into ExamRegion AST
        exam_region = self.question_parser.parse_exam_region(pre_blocks, raw_segments, post_blocks)

        # 4. Apply shuffle rules
        shuffled_region = self.shuffle_engine.shuffle_exam_region(exam_region)

        # 5. Build cleaned final XML blocks
        final_blocks = self.docx_writer.build_final_xml_blocks(shuffled_region)

        return final_blocks
