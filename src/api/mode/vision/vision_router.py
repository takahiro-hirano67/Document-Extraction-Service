# src/api/mode/vision/vision_router.py

"""OCRテキスト抽出APIのエンドポイント

Visonモデルを活用し、高精度にテキストを抽出します。
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

# スキーマ
from src.api.shared_modules.schemas.extract_schema import ExtractTextRequest, ExtractTextResponse

# サービスロジック
from .services import vision_service

router = APIRouter(prefix="/extract", tags=["テキスト抽出"])

# 画像とPDFを許可
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


@router.post(
    path="/vision",
    response_model=ExtractTextResponse,
    response_model_exclude_none=True,
    summary="【VLM】画像/PDFから視覚的構造を維持してテキストを抽出するAPI",
)
async def extract_vision(
    request: ExtractTextRequest = Depends(),
) -> ExtractTextResponse:
    """## VLM (視覚言語モデル) テキスト抽出API

    ローカルのOllamaを利用し、アップロードされた画像やPDFを直接「視覚的に」解析します。
    Doclingでは抽出が難しいスキャンデータや、写真などの画像ファイルから高精度にMarkdown化します。

    ### 対応形式
    - `.pdf`, `.png`, `.jpg`, `.jpeg`
    """
    if not request.file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が取得できません。")

    extension = Path(request.file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"サポートされていないファイル形式です ({extension})。PDF, PNG, JPG, JPEGに対応しています。",
        )

    # VLMサービスを利用して抽出
    extracted_text = await vision_service.extract_text_with_vlm(request.file, extension)

    response_data = ExtractTextResponse(
        status="success",
        filename=request.file.filename,
        file_type=extension.replace(".", ""),
        extracted_text=extracted_text,
        char_count=len(extracted_text),
    )

    return response_data
