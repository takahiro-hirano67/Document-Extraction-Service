# src/core/config.py

"""共通設定・環境変数の読み込み / アクセラレーター識別"""

import torch
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数"""

    # .env ファイルを自動で読み込み、定義していない変数は無視する
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # .env から直接読み取る値
    SELF_PORT: str = Field(..., description="ポート番号", examples=["8001"])
    ACCESS_ALLOW_URL: str = Field(..., description="通信を許可するURL", examples=["http://localhost:8000"])
    OLLAMA_URL: str = Field(..., description="Ollamaの接続URL")
    MAX_FILE_SIZE_MB: int = Field(20, description="許可する最大ファイルサイズ(MB)")
    MAX_UNCOMPRESSED_SIZE_MB: int = Field(100, description="Zip展開後の最大ファイルサイズ(MB) -> ZipBomb対策")

    # None許容の値
    HF_TOKEN: str | None = Field(None, description="HuggingFaceのアクセストークン(モデルダウンロード用)")


settings = Settings()  # pyright: ignore[reportCallIssue]

# ---------- 処理デバイスの識別 ----------

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
