# src/api/services/extract_service.py

"""テキスト抽出APIのサービスクラス

PDF, DOCX, XLSXファイルからメモリ上でテキストを抽出するロジックを提供します。
"""


import io

from fastapi import UploadFile

# ファイル形式別テキスト抽出処理モジュール
from ..extractors.docx_extractor import extract_from_docx
from ..extractors.image_extractor import extract_from_image
from ..extractors.pdf_extractor import extract_from_pdf_with_docling
from ..extractors.pptx_extractor import extract_from_pptx
from ..extractors.text_extractor import extract_from_text
from ..extractors.xlsx_extractor import extract_from_xlsx


def extract_text_from_file(file: UploadFile, extension: str) -> str:
    """アップロードされたファイルからテキストを抽出する

    Args:
        file (UploadFile): FastAPIから受け取ったアップロードファイルオブジェクト
        extension (str): 小文字化された拡張子 (例: '.pdf')

    Returns:
        str: 抽出されたテキスト

    """
    if not file.filename:
        # router層でバリデーションしているが、万が一ここに到達したら500を返す
        raise ValueError("ファイル名が取得できませんでした。有効なファイルをアップロードしてください。")

    # ファイルをメモリ上に読み込む
    content = file.file.read()
    file_stream = io.BytesIO(content)

    extracted_text = ""

    # --- 各ファイル形式の処理 ---
    if extension == ".docx":
        extracted_text = extract_from_docx(file_stream)
    elif extension == ".xlsx":
        extracted_text = extract_from_xlsx(file_stream)
    elif extension == ".pptx":
        extracted_text = extract_from_pptx(file_stream)
    elif extension == ".pdf":
        extracted_text = extract_from_pdf_with_docling(file_stream)
    elif extension in {".txt", ".md"}:
        extracted_text = extract_from_text(content)
    elif extension in {".png", ".jpg", ".jpeg"}:
        extracted_text = extract_from_image(content)
    else:
        raise ValueError(f"サポートされていないファイル形式です: {file.filename}")
    if extracted_text is None:
        raise ValueError(f"抽出されたデータが存在しません: {file.filename}")

    return extracted_text.strip()
