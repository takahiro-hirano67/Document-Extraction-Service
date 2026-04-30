# src/api/mode/deep/deep_router.py

"""高精度テキスト抽出APIのエンドポイント

DoclingとMPS(GPU)を活用し、テーブル構造などを保持したままテキストを抽出します。
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

# スキーマ
from src.api.shared_modules.schemas.extract_schema import ExtractTextRequest, ExtractTextResponse

# サービスロジック
from .services import deep_service

router = APIRouter(prefix="/extract", tags=["テキスト抽出"])

# 許可する拡張子の定義
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".md", ".html", ".htm", ".csv"}


@router.post(
    path="/deep",
    response_model=ExtractTextResponse,
    response_model_exclude_none=True,
    summary="【高精度】PDFからMarkdown形式でテキストを抽出するAPI",
)
async def extract_deep(
    request: ExtractTextRequest = Depends(),
) -> ExtractTextResponse:
    """## 高精度テキスト抽出API (Docling稼働)

    アップロードされたPDFから、Doclingエンジン（MPS/GPU対応）を利用してテキストを抽出します。
    特許公報等の複雑なレイアウトやテーブル構造を維持したまま、Markdown形式で出力します。

    ### 仕様
    - **処理時間**: 数秒〜数十秒かかる場合があります。
    - **対応形式**: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.html`, `.htm`, `.csv`

    ### 注意点
    - パフォーマンスを優先するため、ファイルサイズが極端に大きい場合はタイムアウトになる可能性があります。
    """
    # --- 想定内の例外処理 (想定外はグローバル例外ハンドラに投げる) ---
    # ファイル存在チェック
    if not request.file.filename:
        raise HTTPException(
            status_code=400,
            detail="ファイル名が取得できません。適切な拡張子を持つファイルをアップロードしてください。",
        )

    # 拡張子バリデーション
    extension = Path(request.file.filename).suffix.lower()  # 拡張子を取得 (全て小文字に変換)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"サポートされていないファイル形式です ({extension})。PDF, DOCX, XLSX, PPTX, HTML, MD, CSVに対応しています。",
        )

    # --- 抽出処理の実行 ---
    extracted_text = await deep_service.extract_markdown_with_docling(upload_file=request.file, extension=extension)

    # --- レスポンス構築 ---
    response_data = ExtractTextResponse(
        status="success",
        filename=request.file.filename,
        file_type=extension.replace(".", ""),  # ".pdf" -> "pdf"
        extracted_text=extracted_text,
        char_count=len(extracted_text),
    )

    return response_data
