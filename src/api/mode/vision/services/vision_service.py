# src/api/mode/vision/services/vision_service.py

"""Visionモデルを用いたOCRサービスロジック"""

import asyncio
import io
import logging

import pypdfium2 as pdfium
from fastapi import UploadFile
from ollama import AsyncClient

logger = logging.getLogger(__name__)

# 使用するOllamaのモデル名
MODEL_NAME = "glm-ocr"


def _convert_pdf_to_images(file_content: bytes) -> list[bytes]:
    """【同期処理】PDFのバイトデータを受け取り、各ページをPNGのバイトデータに変換する"""
    image_bytes_list = []

    # pypdfium2 でPDFを読み込み
    pdf = pdfium.PdfDocument(file_content)

    for i in range(len(pdf)):
        page = pdf[i]
        # scale=2 でおよそ144DPI相当。文字を読み取るには十分な解像度
        bitmap = page.render(scale=2)
        pil_image = bitmap.to_pil()

        # PIL画像をPNG形式のバイト列に変換
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format="PNG")
        image_bytes_list.append(img_byte_arr.getvalue())

    pdf.close()
    return image_bytes_list


async def extract_text_with_vlm(upload_file: UploadFile, extension: str) -> str:
    """Ollama(VLM)を用いて画像またはPDFからテキストを抽出する"""
    await upload_file.seek(0)
    file_content = await upload_file.read()

    image_bytes_list = []

    # --- 1. ファイルから画像バイトデータを抽出 ---
    if extension == ".pdf":
        # CPUバウンドな重い処理のため、別スレッドで実行してイベントループのブロックを防ぐ
        image_bytes_list = await asyncio.to_thread(_convert_pdf_to_images, file_content)

    elif extension in {".png", ".jpg", ".jpeg"}:
        image_bytes_list.append(file_content)
    else:
        raise ValueError(f"未対応のファイル形式です: {extension}")

    # --- 2. Ollama SDK (Async) による推論 ---
    extracted_texts = []
    client = AsyncClient(host="http://localhost:11434")

    for i, img_bytes in enumerate(image_bytes_list):
        logger.info(f"Ollamaでページ {i + 1}/{len(image_bytes_list)} を推論中...")

        response = await client.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": "Text Recognition:",
                    "images": [img_bytes],
                }
            ],
        )
        extracted_texts.append(response.message.content)

    # --- 3. 複数ページの結果を結合 ---
    return "\n\n---\n\n".join(extracted_texts).strip()
