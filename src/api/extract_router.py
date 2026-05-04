# src/api/extract_router.py

"""テキスト抽出APIのエンドポイント定義

ユーザーがアップロードしたドキュメントファイルからテキストを抽出して返却します。
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.config import settings

# スキーマ
from .schemas.extract_schema import ExtractTextRequest, ExtractTextResponse

# サービスロジック
from .services import extract_service

# セキュリティ検証モジュールのインポート
from .utils.security import validate_file_security

router = APIRouter(prefix="/extract", tags=["テキスト抽出"])

# 許可する拡張子の定義
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".png", ".jpg", ".jpeg"}

# 許可するMIMEタイプの定義 (拡張子の偽装対策)
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
    "text/plain",
    "text/markdown",
    "image/png",
    "image/jpeg",
}


@router.post(
    path="/text",
    response_model=ExtractTextResponse,
    summary="ファイルからテキストを抽出するAPI",
)
async def extract_text(
    request: ExtractTextRequest = Depends(),
) -> ExtractTextResponse:
    """## アップロードされたドキュメント・画像からテキストを抽出します。

    ### 仕様
    - **対応形式**: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg`
    - **抽出範囲**:
        - PDF: 全ページのテキスト（テキストレイヤーがあるもののみ）
        - Word: 本文・表・ヘッダー・フッター・図形内テキスト（テキストボックス、DrawingML図形）
        - Excel: 全シートのセルデータ（数式ではなく計算後の値）
        - PowerPoint: 全スライドのテキスト、グループ化図形内テキスト、表、スライドノート
        - 画像: VLM(視覚言語モデル)を用いて、写真やスキャンデータから視覚的にテキストを抽出
    - **文書判定**:
        - 特許公報PDFだった場合、is_patentがTrueになります。

    ### 注意点・限界
    - Excel: Markdown形式の表出力には対応していません。多様な形式に対応するため、CSVライクなカンマ区切りを採用しています。
    - PDF: スキャンされた画像形式のPDF（文字が画像になっているもの）からの抽出には、現時点では対応していません。
    - 画像: ローカルAIモデル(Ollama)を使用するため、処理に数秒〜十数秒程度かかる場合があります。
    """
    file_object = request.file
    # --- 想定内の例外処理 (想定外はグローバル例外ハンドラに投げる) ---
    # 1. ファイル名の存在チェック
    if not file_object.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイル名が取得できません。適切なファイルを選択してください。",
        )
    # 2. ファイルサイズのバリデーション
    # 設定値(MB)をバイト単位に変換
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_object.size is not None and file_object.size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,  # 413 Payload Too Large
            detail=f"ファイルサイズが上限（{settings.MAX_FILE_SIZE_MB}MB）を超えています。",
        )
    # 3. 拡張子のバリデーション
    extension = Path(file_object.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"サポートされていないファイル形式です ({extension})。対応形式: PDF, DOCX, XLSX, PPTX, TXT, MD, PNG, JPG",
        )
    # 4. MIMEタイプのバリデーション (偽装対策)
    if file_object.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,  # 415 Unsupported Media Type
            detail=f"許可されていないファイルコンテンツタイプです: {file_object.content_type}",
        )

    # 5. マジックナンバーとZip Bombの検証
    await validate_file_security(file_object, extension)

    # --- テキスト抽出処理実行 ---
    text, is_patent = extract_service.extract_text_from_file(file_object, extension)

    # --- レスポンス構築 ---
    response_json = ExtractTextResponse(
        status="success",
        filename=file_object.filename,
        file_type=extension.replace(".", ""),  # ".pdf" -> "pdf"
        is_patent=is_patent,  # 特許公報として判定されたか
        extracted_text=text,
    )

    return response_json
