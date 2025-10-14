#!/usr/bin/env python3
"""
Convert text files from two specified directories into a single
combined Passim-friendly JSONL file.

Usage:
    python convert_texts_to_passim_corpus.py <dir1> <dir2> [output_file]

Arguments:
    dir1: First text directory (e.g., texts/MEGA_texts)
    dir2: Second text directory (e.g., texts/DNZ_texts)
    output_file: Output file path (optional, defaults to combined_passim_input.jsonl)

Usage Example:
    python convert_texts_to_passim_corpus.py texts/MEGA_texts texts/DNZ_texts output/combined_passim_input.jsonl
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import ftfy
from tqdm import tqdm


def clean_text(text: str) -> str:
    """Clean text to make finding matches easier."""
    result_text = ftfy.fix_text(
        text,
        unescape_html=False,
        fix_encoding=False,
        normalization="NFKC",
    )
    result_text = re.sub(r"\s+", " ", result_text)
    return result_text


def convert_text_to_jsonl(text_dir: str, series_name: str) -> Iterator[Dict[str, Any]]:
    """Convert text files to raw JSONL format and yield records."""
    text_dir = Path(text_dir)

    if not text_dir.exists():
        raise FileNotFoundError(f"Directory not found: {text_dir}")

    txt_files = list(text_dir.glob("*.txt"))
    if not txt_files:
        print(f"Warning: No .txt files found in {text_dir}")
        return

    for txt_file in tqdm(txt_files, desc=f"Processing {series_name} texts"):
        try:
            with open(txt_file, "r", encoding="utf-8") as txt_f:
                content = txt_f.read().strip()
            yield {"id": txt_file.stem, "text": content, "series": series_name}
        except Exception as e:
            print(f"Error processing {txt_file}: {e}")


def transform_record(
    record: Dict[str, Any],
    corpus_name: str = "",
    id_field: str = "id",
    preserve_fields: bool = True,
    corpus_from_field: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert one record to passim-friendly dict:
      - id: taken from record[id_field]
      - text: cleaned text (missing -> "")
    """
    if id_field not in record:
        raise ValueError(f"Record missing required id_field '{id_field}'")

    out_record: Dict[str, Any] = {}
    if preserve_fields:
        if id_field != "id" and "id" in record:
            raise ValueError("Record already has 'id' while id_field != 'id'")
        out_record.update(record)

    out_record["id"] = record[id_field]
    if corpus_from_field:
        if corpus_from_field not in record:
            raise ValueError(f"Record missing corpus_from_field '{corpus_from_field}'")
        pass
    else:
        pass  # out_record["corpus"] = corpus_name

    out_record["text"] = clean_text(record.get("text", ""))
    return out_record


def process_directory_to_passim(
    text_dir: str, series_name: str
) -> Iterator[Dict[str, Any]]:
    """Process a directory of text files and yield Passim-friendly records."""
    for record in convert_text_to_jsonl(text_dir, series_name):
        yield transform_record(record, preserve_fields=True)


def main():
    """Main function to convert texts to Passim format."""
    parser = argparse.ArgumentParser(
        description="Convert text files to Passim-friendly JSONL format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_texts_to_passim.py texts/MEGA_texts texts/DNZ_texts
  python convert_texts_to_passim.py texts/MEGA_texts texts/DNZ_texts output.jsonl
        """,
    )

    parser.add_argument("dir1", help="First text directory")
    parser.add_argument("dir2", help="Second text directory")
    parser.add_argument(
        "output_file",
        nargs="?",
        default="combined_passim_input.jsonl",
        help="Output file path (default: combined_passim_input.jsonl)",
    )

    args = parser.parse_args()

    # Validate input directories
    dir1_path = Path(args.dir1)
    dir2_path = Path(args.dir2)

    if not dir1_path.exists():
        print(f"Error: Directory not found: {dir1_path}")
        sys.exit(1)

    if not dir2_path.exists():
        print(f"Error: Directory not found: {dir2_path}")
        sys.exit(1)

    # Get series names from directory names
    series1 = dir1_path.name.lower().replace("_texts", "").replace("texts", "")
    series2 = dir2_path.name.lower().replace("_texts", "").replace("texts", "")

    if not series1:
        series1 = "series1"
    if not series2:
        series2 = "series2"

    print("Processing directories:")
    print(f"  {dir1_path} -> series: {series1}")
    print(f"  {dir2_path} -> series: {series2}")
    print(f"Output file: {args.output_file}")
    print()

    # Process both directories and write to output file
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_records = 0

    with open(output_path, "w", encoding="utf-8") as outf:
        # Process first directory
        print(f"Processing {dir1_path}...")
        for record in process_directory_to_passim(str(dir1_path), series1):
            outf.write(json.dumps(record, ensure_ascii=False) + "\n")
            total_records += 1

        # Process second directory
        print(f"Processing {dir2_path}...")
        for record in process_directory_to_passim(str(dir2_path), series2):
            outf.write(json.dumps(record, ensure_ascii=False) + "\n")
            total_records += 1

    print("\nConversion completed!")
    print(f"Total records: {total_records}")
    print(f"Output file: {output_path.resolve()}")


if __name__ == "__main__":
    main()
