"""
DocxFileAdapter: Bridges physical .docx disk files with QuizShufflerPipeline.
"""
from pathlib import Path
from typing import Optional, List
from src.pipeline import QuizShufflerPipeline
from src.models.exam_structure import XmlContentBlock
from src.docx_extractor import DocxXmlExtractor


class DocxFileAdapter:
    """
    Handles reading .docx files from disk, running pipeline, and writing back.
    """

    def __init__(self, seed: Optional[int] = None):
        self.pipeline = QuizShufflerPipeline(seed=seed)

    def process_docx_blocks(self, raw_blocks: List[XmlContentBlock]) -> List[XmlContentBlock]:
        """
        Executes pipeline directly on XmlContentBlocks.
        """
        return self.pipeline.process_blocks(raw_blocks)

    def process_file(self, input_path: Path, output_path: Path) -> bool:
        """
        Reads input_path .docx, executes pipeline, and saves to output_path.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        extractor = DocxXmlExtractor(str(input_path))
        raw_blocks = extractor.extract_blocks()
        
        # Execute shuffling pipeline
        final_blocks = self.pipeline.process_blocks(raw_blocks)
        
        # Save shuffled XML blocks back to output DOCX
        extractor.save_with_blocks(final_blocks, str(output_path))
        return True
