# src/api/mode/deep/services/deep_service.py

"""高精度テキスト抽出のサービスクラス

Doclingを利用してPDFファイルからテキスト（Markdown）を抽出します。
インメモリでのストリーム処理およびMarkdownの整形を行います。
"""

import asyncio
import io

from docling_core.types.io import DocumentStream
from fastapi import UploadFile

from src.core.model_state import model_state

# 補助処理
from ..utils.markdown_cleaner import clean_markdown


async def extract_markdown_with_docling(upload_file: UploadFile, extension: str) -> str:
    """アップロードされたファイルからDoclingを用いてMarkdownを抽出する

    Args:
        upload_file (UploadFile): FastAPIから受け取ったアップロードファイルオブジェクト
        extension (str): 小文字化された拡張子 (例: '.pdf')

    Returns:
        str: 抽出・構造化された正規化済みMarkdownテキスト

    Raises:
        RuntimeError: Doclingのコンバーターが初期化されていない場合

    """
    if model_state.converter is None:
        raise RuntimeError("Docling converter is not initialized.")

    # --- 1. ファイルをメモリ(BytesIO)に読み込む ---
    await upload_file.seek(0)
    file_content = await upload_file.read()
    pdf_stream = io.BytesIO(file_content)

    # --- 2. DoclingのDocumentStreamオブジェクトを生成 ---
    # ファイル名が存在しない場合はフォールバックとして "例: input.pdf" を設定
    safe_filename = upload_file.filename if upload_file.filename else f"input{extension}"
    doc_stream = DocumentStream(name=safe_filename, stream=pdf_stream)

    # --- 3. Doclingによる抽出処理 ---
    # convert()は同期処理で重いため、イベントループをブロックしないよう別スレッドで実行する
    conversion_result = await asyncio.to_thread(
        model_state.converter.convert,
        doc_stream,
    )

    # --- 4. Markdown形式での出力 ---
    raw_markdown = conversion_result.document.export_to_markdown()

    # --- 5. Markdown出力の整形 ---
    cleaned_markdown = clean_markdown(raw_markdown)

    return cleaned_markdown.strip()
