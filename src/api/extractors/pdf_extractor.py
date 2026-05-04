# src/api/extractors/pdf_extractor_docling.py

"""PDFファイル(.pdf)からDoclingでテキストを抽出するモジュール

Doclingを利用してPDFファイルからテキスト（Markdown）を抽出します。
インメモリでのストリーム処理を行います。
"""

import io

from docling_core.types.io import DocumentStream

from src.core.model_state import model_state

from ..cleaners.text_cleaner import clean_docling_markdown


def extract_from_pdf_with_docling(file_stream: io.BytesIO) -> tuple[str, bool]:
    """アップロードされたファイルからDoclingを用いてMarkdownを抽出する

    Args:
        file_stream(io.BytesIO): PDF ファイルの BytesIO ストリーム

    Returns:
        tuple[str, bool]: 抽出・構造化されたMarkdownテキスト, 特許公報判定フラグ

    Raises:
        RuntimeError: Doclingのコンバーターが初期化されていない場合

    """
    if model_state.converter is None:
        raise RuntimeError("Docling converter is not initialized.")

    # --- 1. DoclingのDocumentStreamオブジェクトを生成 ---
    doc_stream = DocumentStream(name="input.pdf", stream=file_stream)

    # --- 2. Doclingによる抽出処理 ---
    conversion_result = model_state.converter.convert(doc_stream)

    # --- 3. Markdown形式での出力 ---
    markdown_text = conversion_result.document.export_to_markdown()

    # --- 4. Markdown出力の整形 ---
    markdown_text, is_patent = clean_docling_markdown(markdown_text)

    return markdown_text.strip(), is_patent
