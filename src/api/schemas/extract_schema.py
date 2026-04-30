# src/api/schemas/extract_schema.py

"""テキスト抽出APIで使用するスキーマ定義

アップロードされたファイルからの抽出結果を定義します。
"""

from dataclasses import dataclass

from fastapi import File, UploadFile
from pydantic import BaseModel, Field

# ==========================================
# リクエストの型
# ==========================================

@dataclass
class ExtractTextRequest:
    """テキスト抽出APIのリクエストパラメータ"""

    file: UploadFile = File(..., description="抽出対象のファイル (PDF, DOCX, XLSX)")


# ==========================================
# レスポンスの型
# ==========================================


class ExtractTextResponse(BaseModel):
    """テキスト抽出APIのレスポンス"""

    status: str = Field("success", description="ステータス", examples=["success"])
    filename: str = Field(..., description="アップロードされたファイル名", examples=["document.pdf"])
    file_type: str = Field(..., description="判定されたファイル形式", examples=["pdf"])
    extracted_text: str = Field(..., description="抽出されたテキスト全文")
