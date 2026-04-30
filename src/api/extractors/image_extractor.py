# src/api/extractors/image_extractor.py

"""画像ファイルテキスト抽出モジュール

Ollama (VLM) を利用して、画像ファイルからテキストを抽出します。
"""

import logging

from ollama import Client, ResponseError

from src.core.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = "glm-ocr"  # 使用するモデル名
PROMPT = "Text Recognition:"  # GLM-OCR推奨プロンプト


def extract_from_image(file_content: bytes) -> str | None:
    """画像ファイルのバイトデータを受け取り、テキストを抽出する

    Args:
        file_content (bytes): 画像ファイルのバイトデータ

    Returns:
        str: 抽出・解析されたMarkdownテキスト

    Raises:
        RuntimeError: Ollamaサーバーへの接続や推論に失敗した場合

    """
    # 同期クライアントの初期化
    client = Client(host=settings.OLLAMA_URL)

    logger.info(f"Ollama ({MODEL_NAME}) による画像解析を開始します...")

    try:
        response = client.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": PROMPT,  # GLM-OCR推奨プロンプト
                    "images": [file_content],  # バイトデータを直接渡す
                }
            ],
        )
        if response.message.content is not None:
            return response.message.content

    except ResponseError as error:
        raise RuntimeError(f"Ollamaでの推論に失敗しました: {error}") from error
    except Exception as error:
        raise RuntimeError("画像解析サーバー(Ollama)への接続に失敗しました。") from error
