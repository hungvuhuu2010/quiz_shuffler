"""
DocxWriter: Handles accurate question renumbering across split XML runs
and formats option choices (A, B, C, D) with XML tab stops.
"""
import re
from typing import List
from src.models.exam_structure import (
    ExamRegion,
    XmlContentBlock,
    TYPE_START_MARKER,
    TYPE_END_MARKER,
    CLUSTER_MARKERS
)

ALL_MARKERS = {TYPE_START_MARKER, TYPE_END_MARKER}.union(CLUSTER_MARKERS)

class DocxWriter:
    """
    Assembles final XML blocks, renumbers questions accurately regardless of XML fragmentation,
    and applies tab stops to align ABCD options.
    """

    def clean_marker_from_xml(self, raw_xml: str) -> str:
        """Strips control markers from raw XML text."""
        cleaned = raw_xml
        for marker in ALL_MARKERS:
            if marker in cleaned:
                cleaned = cleaned.replace(marker, "")
                encoded_marker = marker.replace("<", "&lt;").replace(">", "&gt;")
                cleaned = cleaned.replace(encoded_marker, "")
        return cleaned

    def _is_only_marker_block(self, raw_xml: str) -> bool:
        """Checks if a block contains ONLY a control marker."""
        texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', raw_xml)
        full_text = "".join(texts).strip()
        
        if full_text in ALL_MARKERS or full_text in {m.replace("<", "&lt;").replace(">", "&gt;") for m in ALL_MARKERS}:
            return True
            
        cleaned_text = full_text
        for m in ALL_MARKERS:
            cleaned_text = cleaned_text.replace(m, "").replace(m.replace("<", "&lt;").replace(">", "&gt;"), "")
            
        return len(cleaned_text.strip()) == 0 and len(full_text) > 0

    def _renumber_xml_paragraph(self, raw_xml: str, new_number: int) -> str:
        """
        Renumbers question start accurately even when split across multiple <w:t> tags.
        Example: 'Câu 14.' -> 'Câu 1.', 'Question 10:' -> 'Question 1:'
        """
        # Find all <w:t> contents and their byte positions
        t_pattern = re.compile(r'(<w:t[^>]*>)(.*?)(</w:t>)', re.DOTALL)
        matches = list(t_pattern.finditer(raw_xml))
        
        if not matches:
            return raw_xml

        # Extract full plain text of paragraph
        plain_text = "".join(m.group(2) for m in matches)
        
        # Regex to detect question number at paragraph start
        q_regex = re.compile(r'^(Câu|Question|Bài|\d+)?\s*(\d+)([\.\:\)\/])', re.IGNORECASE)
        m_q = q_regex.search(plain_text.strip())
        
        if not m_q:
            return raw_xml

        prefix_word = m_q.group(1) or "Câu"
        sep_char = m_q.group(3) or "."
        new_prefix = f"{prefix_word} {new_number}{sep_char}"

        # Rebuild XML: Replace the first <w:t> containing question label
        replaced = False
        new_xml_parts = []
        last_end = 0

        for match in matches:
            start, end = match.span()
            new_xml_parts.append(raw_xml[last_end:start])
            
            tag_open = match.group(1)
            t_content = match.group(2)
            tag_close = match.group(3)

            if not replaced and q_regex.search(t_content):
                # Replace prefix in this first matching run
                t_content = q_regex.sub(new_prefix, t_content, count=1)
                replaced = True
            elif not replaced and any(kw in t_content for kw in ["Câu", "Question", "Bài"]):
                # If prefix is split, replace keyword
                t_content = re.sub(r'(Câu|Question|Bài)\s*\d*', f"{prefix_word} {new_number}", t_content, count=1)
                replaced = True

            new_xml_parts.append(f"{tag_open}{t_content}{tag_close}")
            last_end = end

        new_xml_parts.append(raw_xml[last_end:])
        return "".join(new_xml_parts)

    def format_tabs_for_choices(self, raw_xml: str) -> str:
        """
        Formats ABCD choice paragraphs with XML tabs for straight alignment.
        """
        # Check if line contains inline choices like "A. ... B. ... C. ... D. ..."
        choice_regex = re.compile(r'([A-D][\.\:\)])\s+')
        texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', raw_xml)
        full_text = "".join(texts)
        
        matches = list(choice_regex.finditer(full_text))
        if len(matches) >= 2:
            # Add tab stop XML elements <w:tab/> before B., C., D. choices
            def add_tab_before_choices(m):
                t_open, t_val, t_close = m.group(1), m.group(2), m.group(3)
                updated_val = re.sub(r'([B-D][\.\:\)])', r'\t\1', t_val)
                return f"{t_open}{updated_val}{t_close}"
                
            raw_xml = re.sub(r'(<w:t[^>]*>)(.*?)(</w:t>)', add_tab_before_choices, raw_xml)

        return raw_xml

    def process_block(self, block: XmlContentBlock) -> List[XmlContentBlock]:
        """Cleans a single block. Returns empty if block is strictly a marker."""
        raw = block.raw_xml if block.raw_xml else ""
        if self._is_only_marker_block(raw):
            return []
            
        cleaned_xml = self.clean_marker_from_xml(raw)
        cleaned_xml = self.format_tabs_for_choices(cleaned_xml)
        return [XmlContentBlock(element=block.element, raw_xml=cleaned_xml)]

    def build_final_xml_blocks(self, region: ExamRegion) -> List[XmlContentBlock]:
        """
        Flattens the ExamRegion AST, RENUMBERS all questions sequentially,
        and formats choice alignment.
        """
        final_blocks: List[XmlContentBlock] = []

        # 1. Pre-region blocks
        for block in region.pre_region_blocks:
            final_blocks.extend(self.process_block(block))

        # Global Counter for sequential renumbering
        q_counter = 1

        # 2. Exam items (Normal questions & Clusters)
        for item in region.exam_items:
            if item.is_normal_question():
                q_blocks = item.question.xml_blocks
                for idx, b in enumerate(q_blocks):
                    cleaned_list = self.process_block(b)
                    if cleaned_list:
                        raw = cleaned_list[0].raw_xml
                        if idx == 0:
                            # Renumber first paragraph of question
                            raw = self._renumber_xml_paragraph(raw, q_counter)
                            q_counter += 1
                        final_blocks.append(XmlContentBlock(element=b.element, raw_xml=raw))

            elif item.is_cluster():
                # Cluster prefix (Passage/Table/Image)
                for b in item.cluster.prefix_xml_blocks:
                    final_blocks.extend(self.process_block(b))
                
                # Cluster questions
                for q in item.cluster.questions:
                    for idx, b in enumerate(q.xml_blocks):
                        cleaned_list = self.process_block(b)
                        if cleaned_list:
                            raw = cleaned_list[0].raw_xml
                            if idx == 0:
                                # Renumber question inside cluster
                                raw = self._renumber_xml_paragraph(raw, q_counter)
                                q_counter += 1
                            final_blocks.append(XmlContentBlock(element=b.element, raw_xml=raw))

        # 3. Post-region blocks
        for block in region.post_region_blocks:
            final_blocks.extend(self.process_block(block))

        return final_blocks
