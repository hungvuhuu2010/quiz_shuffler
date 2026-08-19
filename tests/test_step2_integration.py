"""
End-to-End Integration tests using full realistic document scenarios 
(Tables, Images, OMML equations, Renumbering, and Control Markers).
"""
import pytest
from src.models.exam_structure import XmlContentBlock
from src.pipeline import QuizShufflerPipeline


def make_p(text: str) -> XmlContentBlock:
    raw = f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"
    return XmlContentBlock(element=None, raw_xml=raw)

def make_table() -> XmlContentBlock:
    raw = (
        "<w:tbl>"
        "<w:tr><w:tc><w:p><w:r><w:t>Dữ liệu A</w:t></w:r></w:p></w:tc></w:tr>"
        "</w:tbl>"
    )
    return XmlContentBlock(element=None, raw_xml=raw)

def make_drawing_p(text: str) -> XmlContentBlock:
    raw = (
        f"<w:p><w:r><w:t>{text}</w:t></w:r>"
        "<w:r><w:drawing><a:graphic>IMAGE_DATA</a:graphic></w:drawing></w:r></w:p>"
    )
    return XmlContentBlock(element=None, raw_xml=raw)

def make_omml_p(text: str) -> XmlContentBlock:
    raw = (
        f"<w:p><w:r><w:t>{text}</w:t></w:r>"
        "<m:oMath><m:r><m:t>x^2 + y^2 = z^2</m:t></m:r></m:oMath></w:p>"
    )
    return XmlContentBlock(element=None, raw_xml=raw)


def test_full_pipeline_with_table_drawing_omml():
    raw_document = [
        make_p("TRƯỜNG THPT X - ĐỀ THI HỌC KỲ"),
        make_p("Thời gian làm bài: 90 phút"),
        make_p("<type 1>"),
        
        make_drawing_p("Câu 1. Cho hình vẽ sau:"),
        make_p("A. Đúng"),
        make_p("B. Sai"),

        make_p("<##>"),
        make_p("Dựa vào bảng số liệu sau:"),
        make_table(),
        make_p("Câu 2. Dữ liệu dòng 1 là gì?"),
        make_p("Câu 3. Dữ liệu dòng 2 là gì?"),

        make_omml_p("Câu 4. Biểu thức sau có giá trị bao nhiêu:"),
        make_p("A. 1"),
        make_p("B. 2"),

        make_p("<??>"),
        make_p("Câu 5. Trong chùm 2?"),
        make_p("Câu 6. Trong chùm 2?"),

        make_p("<end 1>"),
        make_p("HẾT ĐỀ THI"),
        make_p("Đáp án và lời giải chi tiết")
    ]

    pipeline = QuizShufflerPipeline(seed=42)
    final_blocks = pipeline.process_blocks(raw_document)

    final_xmls = [b.raw_xml for b in final_blocks]
    combined_xml = "".join(final_xmls)

    assert "<type 1>" not in combined_xml
    assert "<end 1>" not in combined_xml
    assert "<##>" not in combined_xml
    assert "<??>" not in combined_xml

    assert "TRƯỜNG THPT X - ĐỀ THI HỌC KỲ" in combined_xml
    assert "HẾT ĐỀ THI" in combined_xml

    assert "<w:tbl>" in combined_xml
    assert "Dữ liệu A" in combined_xml
    assert "<w:drawing>" in combined_xml
    assert "IMAGE_DATA" in combined_xml
    assert "<m:oMath>" in combined_xml
    assert "x^2 + y^2 = z^2" in combined_xml

def test_false_positive_prevention_in_pipeline():
    raw_document = [
        make_p("<type 1>"),
        make_p("Câu 1. Dựa vào đoạn văn sau, hãy chọn câu đúng."),
        make_p("Câu 2. Dựa vào bảng số liệu và hình vẽ bên dưới..."),
        make_table(),
        make_p("<end 1>")
    ]

    pipeline = QuizShufflerPipeline(seed=100)
    final_blocks = pipeline.process_blocks(raw_document)
    combined = "".join([b.raw_xml for b in final_blocks])

    # Flexible verification: Check that questions and tables are preserved regardless of renumbered prefixes
    assert "Dựa vào đoạn văn sau, hãy chọn câu đúng." in combined
    assert "Dựa vào bảng số liệu và hình vẽ bên dưới..." in combined
    assert "<w:tbl>" in combined
