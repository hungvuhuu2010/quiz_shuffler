"""
CLI Interface for Quiz Shuffler Application.
Usage:
    python -m src.cli -i de_goc.docx -o de_tron.docx
    python -m src.cli -i de_goc.docx -d ./out_folder -n 4
"""
import argparse
import sys
from pathlib import Path
from src.file_adapter import DocxFileAdapter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Quiz Shuffler - Hệ thống trộn đề trắc nghiệm DOCX bảo toàn cấu trúc XML."
    )
    parser.add_argument(
        "-i", "--input", required=True, type=str,
        help="Đường dẫn tới file .docx đề thi gốc."
    )
    parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Đường dẫn file .docx đầu ra (dùng khi chỉ trộn 1 bản)."
    )
    parser.add_argument(
        "-d", "--output-dir", type=str, default="output",
        help="Thư mục chứa các mã đề xuất ra (mặc định: ./output)."
    )
    parser.add_argument(
        "-n", "--num-versions", type=int, default=1,
        help="Số lượng mã đề cần tạo (mặc định: 1)."
    )
    parser.add_argument(
        "-s", "--seed", type=int, default=None,
        help="Cố định seed ngẫu nhiên để tái lập kết quả."
    )
    return parser


def main(args_list=None):
    parser = build_parser()
    args = parser.parse_args(args_list)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] File đầu vào không tồn tại: {input_path}")
        sys.exit(1)

    out_dir = Path(args.output_dir)

    print(f"=== QUIZ SHUFFLER ===")
    print(f"File gốc: {input_path}")
    print(f"Số bản đề cần trộn: {args.num-versions if hasattr(args, 'num-versions') else args.num_versions}")

    num_versions = args.num_versions

    if num_versions == 1 and args.output:
        out_file = Path(args.output)
        adapter = DocxFileAdapter(seed=args.seed)
        adapter.process_file(input_path, out_file)
        print(f"[SUCCESS] Đã tạo mã đề thành công: {out_file}")
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = input_path.stem
        for v in range(1, num_versions + 1):
            out_file = out_dir / f"{stem}_MaDe_{v:03d}.docx"
            version_seed = (args.seed + v) if args.seed is not None else None
            adapter = DocxFileAdapter(seed=version_seed)
            adapter.process_file(input_path, out_file)
            print(f"  -> [OK] Đã tạo mã đề {v:03d}: {out_file}")

    print("=== HOÀN THÀNH ===")


if __name__ == "__main__":
    main()
