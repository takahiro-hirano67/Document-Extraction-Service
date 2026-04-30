# src/api/domains/extract/extract_router.py

"""テキスト抽出APIのエンドポイント定義

ユーザーがアップロードしたドキュメントファイルからテキストを抽出して返却します。
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

# スキーマ
from .schemas.extract_schema import ExtractTextRequest, ExtractTextResponse

# サービスロジック
from .services import extract_service

router = APIRouter(prefix="/extract", tags=["テキスト抽出"])

# 許可する拡張子の定義
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md", ".png", ".jpg", ".jpeg"}


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
    - **一時保存なし**: サーバー側のストレージには保存せず、メモリ上で処理して破棄します。
    - **対応形式**: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg`
    - **抽出範囲**:
        - PDF: 全ページのテキスト（テキストレイヤーがあるもののみ）
        - Word: 本文・表・ヘッダー・フッター・図形内テキスト（テキストボックス、DrawingML図形）
        - Excel: 全シートのセルデータ（数式ではなく計算後の値）
        - PowerPoint: 全スライドのテキスト、グループ化図形内テキスト、表、スライドノート
        - 画像: VLM(視覚言語モデル)を用いて、写真やスキャンデータから視覚的にテキストを抽出

    ### 注意点・限界
    - Excel: Markdown形式の表出力には対応していません。多様な形式に対応するため、CSVライクなカンマ区切りを採用しています。
    - PDF: スキャンされた画像形式のPDF（文字が画像になっているもの）からの抽出には、現時点では対応していません。
    - 画像: ローカルAIモデル(Ollama)を使用するため、処理に数秒〜十数秒程度かかる場合があります。
    """
    # --- 想定内の例外処理 (想定外はグローバル例外ハンドラに投げる) ---
    # ファイル名の存在チェック
    if not request.file.filename:
        raise HTTPException(
            status_code=400, detail="ファイル名が取得できません。適切な拡張子を持つファイルをアップロードしてください。"
        )
    # 拡張子のバリデーション
    extension = Path(request.file.filename).suffix.lower()  # 拡張子を取得 (全て小文字に変換)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"サポートされていないファイル形式です ({extension})。対応しているファイル形式:PDF, DOCX, XLSX, TXT, MD, PNG, JPG",
        )

    # --- テキスト抽出処理実行 ---
    text = extract_service.extract_text_from_file(request.file, extension, mode=request.mode)

    # --- レスポンス構築 ---
    response_json = ExtractTextResponse(
        status="success",
        filename=request.file.filename,
        file_type=extension.replace(".", ""),  # ".pdf" -> "pdf"
        extracted_text=text,
        char_count=len(text),
    )

    return response_json
