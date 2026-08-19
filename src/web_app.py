"""
Streamlit Web Application for Quiz Shuffler.
Provides an interactive online UI to upload .docx exams, configure shuffling rules,
and download shuffled exam variants packaged in a zip archive.
"""
import sys
from pathlib import Path

# Fix import path for Streamlit Cloud deployment
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
import io
import time
import zipfile
import tempfile
from src.file_adapter import DocxFileAdapter

st.set_page_config(
    page_title="Trộn Đề Trắc Nghiệm DOCX",
    page_icon="📝",
    layout="centered"
)

def main():
    st.title("📝 QUIZ SHUFFLER ONLINE")
    st.caption("Hệ thống trộn đề trắc nghiệm DOCX bảo toàn cấu trúc XML, Bảng, Hình ảnh và Công thức OMML")

    st.markdown("---")

    st.sidebar.header("⚙️ Cấu hình Trộn Đề")
    num_versions = st.sidebar.number_input(
        "Số lượng mã đề cần tạo:",
        min_value=1,
        max_value=24,
        value=4,
        step=1
    )

    use_seed = st.sidebar.checkbox("Cố định Seed ngẫu nhiên (Tái lập kết quả)")
    seed_val = None
    if use_seed:
        seed_val = st.sidebar.number_input("Giá trị Seed:", min_value=1, value=42, step=1)

    uploaded_file = st.file_uploader(
        "Tải lên file đề thi gốc (.docx):",
        type=["docx"],
        help="File Word phải chứa các marker vùng <type 1> ... <end 1> và marker chùm <##>, <#?>, <??>"
    )

    if uploaded_file is not None:
        st.success(f"📂 Đã tải lên file: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
        
        if st.button("🚀 BẮT ĐẦU TRỘN ĐỀ", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_dir_path = Path(temp_dir)
                    input_docx_path = temp_dir_path / uploaded_file.name
                    
                    with open(input_docx_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    zip_buffer = io.BytesIO()
                    stem_name = input_docx_path.stem

                    base_timestamp = int(time.time() * 1000)

                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for idx in range(1, num_versions + 1):
                            status_text.text(f"Đang xáo trộn và đóng gói mã đề {idx:03d} / {num_versions:03d}...")
                            
                            out_filename = f"{stem_name}_MaDe_{idx:03d}.docx"
                            out_path = temp_dir_path / out_filename
                            
                            if seed_val is not None:
                                current_seed = seed_val + idx
                            else:
                                current_seed = base_timestamp + (idx * 997)

                            adapter = DocxFileAdapter(seed=current_seed)
                            adapter.process_file(input_docx_path, out_path)

                            zip_file.write(out_path, arcname=out_filename)
                            progress_bar.progress(int((idx / num_versions) * 100))

                    status_text.text("✅ Hoàn tất quá trình trộn đề!")
                    st.balloons()

                    zip_buffer.seek(0)
                    st.download_button(
                        label=f"📦 TẢI VỀ TOÀN BỘ {num_versions} MÃ ĐỀ (.ZIP)",
                        data=zip_buffer,
                        file_name=f"{stem_name}_KetQuaTronDe.zip",
                        mime="application/zip",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}")
                st.exception(e)

    with st.expander("📌 Hướng dẫn sử dụng Marker"):
        st.markdown("""
        * **`<type 1>` ... `<end 1>`**: Xác định phạm vi vùng câu hỏi cần trộn trong file Word.
        * **`<##>`**: Cố định vị trí chùm, **cố định** thứ tự câu bên trong chùm.
        * **`<#?>`**: Cố định vị trí chùm, **xáo trộn** thứ tự câu bên trong chùm.
        * **`<??>`**: **Xáo trộn** vị trí chùm, **xáo trộn** thứ tự câu bên trong chùm.
        * **Câu đơn không có marker**: Được xử lý độc lập và xáo trộn vị trí linh hoạt.
        """)

if __name__ == "__main__":
    main()
