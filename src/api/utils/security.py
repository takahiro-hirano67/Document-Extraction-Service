# src/api/utils/security.py

"""アップロードされたファイルの検証を行うモジュール"""

import io
import zipfile

from fastapi import HTTPException, UploadFile, status

from src.core.config import settings

# マジックナンバーの定義 (各ファイルの先頭バイト)
MAGIC_NUMBERS = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8",
    "jpeg": b"\xff\xd8",
    # DOCX, XLSX, PPTX は内部的に ZIP 形式のため同じマジックナンバー
    "docx": b"PK\x03\x04",
    "xlsx": b"PK\x03\x04",
    "pptx": b"PK\x03\x04",
}


async def validate_file_security(file_obj: UploadFile, extension: str) -> None:
    """マジックナンバー検証とZip Bomb検証を行う"""
    # ファイルの先頭から読み込むために一度中身を取得
    content = await file_obj.read()
    ext_key = extension.replace(".", "")

    # --- 1. マジックナンバー（シグネチャ）検証 ---
    if ext_key in MAGIC_NUMBERS:
        expected_magic = MAGIC_NUMBERS[ext_key]
        if not content.startswith(expected_magic):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="ファイルの拡張子と実際のファイルデータが一致しません（偽装ファイルの疑い）。",
            )
    elif ext_key in ["txt", "md"]:
        # テキストファイルの場合は、マジックナンバーがないため文字列としてデコードできるか検証
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content.decode("shift_jis")
            except UnicodeDecodeError as error:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="有効なテキストファイルとして読み取れませんでした。",
                ) from error

    # --- 2. Zip Bomb（メモリ枯渇）対策 ---
    if ext_key in ["docx", "xlsx", "pptx"]:
        max_uncompressed_bytes = settings.MAX_UNCOMPRESSED_SIZE_MB * 1024 * 1024
        max_files = 10000  # 展開される内部ファイル数の上限

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # ファイル数の検証
                if len(zf.infolist()) > max_files:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="ファイル内部の構成要素が多すぎます（Zip Bombの疑い）。",
                    )

                # 展開後の総容量の検証
                total_size = 0
                for zinfo in zf.infolist():
                    total_size += zinfo.file_size
                    if total_size > max_uncompressed_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"解凍後のファイル総容量が上限（{settings.MAX_UNCOMPRESSED_SIZE_MB}MB）を超えるため処理を中断しました。",
                        )
        except zipfile.BadZipFile as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="破損したファイル、または有効なOfficeファイル構造ではありません。",
            ) from error

    # 読み込んだポインタを先頭に戻す（後続のextract_serviceでの読み込みのため）
    await file_obj.seek(0)
