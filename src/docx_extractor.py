"""
DocxXmlExtractor: Extracts raw XML nodes (Paragraphs, Tables) from DOCX documents
and handles saving modified XML content blocks back into a valid DOCX file.
"""
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import List
from lxml import etree

from src.models.exam_structure import XmlContentBlock

# Namespaces commonly present in Word XML
WORD_NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'
}

class DocxXmlExtractor:
    """
    Extracts XML blocks directly from word/document.xml of a DOCX file
    and reconstructs the DOCX archive when saving modified blocks.
    """

    def __init__(self, docx_path: str):
        self.docx_path = Path(docx_path)
        if not self.docx_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    def extract_blocks(self) -> List[XmlContentBlock]:
        """
        Reads word/document.xml from the .docx zip archive and extracts top-level
        elements inside w:body (Paragraphs w:p, Tables w:tbl).
        """
        blocks: List[XmlContentBlock] = []
        with zipfile.ZipFile(self.docx_path, 'r') as zip_ref:
            if 'word/document.xml' not in zip_ref.namelist():
                raise ValueError("Invalid DOCX file: missing word/document.xml")

            xml_bytes = zip_ref.read('word/document.xml')
            tree = etree.fromstring(xml_bytes)

            body = tree.find('.//w:body', namespaces=WORD_NAMESPACES)
            if body is None:
                # Fallback if default namespace is used without prefix
                body = tree.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')

            if body is not None:
                for child in body:
                    # Filter for paragraphs, tables, or structural elements
                    tag = child.tag
                    if tag.endswith('p') or tag.endswith('tbl'):
                        raw_xml = etree.tostring(child, encoding='utf-8').decode('utf-8')
                        blocks.append(XmlContentBlock(element=child, raw_xml=raw_xml))

        return blocks

    def save_with_blocks(self, new_blocks: List[XmlContentBlock], output_path: str):
        """
        Replaces the w:body children in word/document.xml with new_blocks
        and writes out a new complete DOCX file preserving all media and relationships.
        """
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract entire original zip structure
            with zipfile.ZipFile(self.docx_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)

            doc_xml_path = temp_path / 'word' / 'document.xml'
            if not doc_xml_path.exists():
                raise FileNotFoundError("word/document.xml missing in extracted folder")

            # Parse original document.xml
            tree = etree.parse(str(doc_xml_path))
            root = tree.getroot()

            body = root.find('.//w:body', namespaces=WORD_NAMESPACES)
            if body is None:
                body = root.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')

            if body is None:
                raise ValueError("Could not locate w:body in document.xml")

            # Preserve w:sectPr (Section Properties like page size, margins)
            sectPr = body.find('.//w:sectPr', namespaces=WORD_NAMESPACES)
            if sectPr is None:
                sectPr = body.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr')

            # Clear current body
            body.clear()

            # Append new modified XML nodes
            for b in new_blocks:
                if b.raw_xml and b.raw_xml.strip():
                    try:
                        node = etree.fromstring(b.raw_xml.encode('utf-8'))
                        body.append(node)
                    except Exception:
                        pass

            # Restore section properties at the end of body if present
            if sectPr is not None:
                body.append(sectPr)

            # Save modified document.xml back
            tree.write(str(doc_xml_path), xml_declaration=True, encoding='utf-8', standalone='yes')

            # Re-pack into output .docx zip archive
            zip_out = out_file.with_suffix('')  # shutil.make_archive adds suffix automatically
            shutil.make_archive(str(zip_out), 'zip', temp_path)
            
            # Rename .zip to .docx
            zip_created = out_file.with_suffix('.zip')
            if zip_created.exists():
                if out_file.exists():
                    out_file.unlink()
                zip_created.rename(out_file)
