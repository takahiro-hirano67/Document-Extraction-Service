# src/main.py

"""FastAPIのエントリーポイント"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ルーター
from src.api.mode.deep import deep_router
from src.api.mode.vision import vision_router

# 環境変数・状態管理
from src.core.config import device, settings
from src.core.model_state import model_state

# ==========================================
# ログ設定の初期化
# ==========================================

"""
DEBUG (10): 開発時の動作確認など、詳細な情報。
INFO (20): 正常な動作の記録。
WARNING (30): エラーではないが、注意が必要な状態。
ERROR (40): 重大な問題が発生し、一部の機能が実行できなかった状態。
CRITICAL (50): プログラム自体が停止してしまうような致命的なエラー。
"""

# --- ログの基本設定 ---
logging.basicConfig(
    # ログレベルの閾値: 設定したレベル以上のログだけが出力される
    level=logging.INFO,
    # 出力形式の定義: "発生日時 - レベル - ロガー名(発生場所) - メッセージ"
    format="|%(asctime)s|%(levelname)s|%(name)s| %(message)s",
)

# --- ロガーのインスタンス化 ---
# __name__: 実行中のモジュール名(ファイル名)が自動挿入
# --> どのファイルのどの部分でエラーが起きたのかを特定できる
logger = logging.getLogger(__name__)

# ==========================================
# ライフサイクルイベント（起動・終了時の処理）
# ==========================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """アプリケーションのライフサイクル管理

    - yield前: アプリ起動時の処理
    - yield後: アプリ終了時の処理
    """
    # --- 起動時の処理 ---
    logger.info("アプリケーションを起動しています...")
    logger.info(f"処理デバイス: {device}")
    logger.info("DoclingのDocumentConverterを初期化しています...")
    model_state.initialize_converter()
    logger.info("Doclingの初期化が完了しました。")
    logger.info("アプリケーションを起動しました。リクエストを受け付けます。")

    yield  # ← ここでアプリケーションが実行される

    # --- 終了時の処理 ---
    logger.info("アプリケーションを終了しています...")
    logger.info("アプリケーションを終了しました。")


# ==========================================
# メタ情報の設定
# ==========================================

# プロジェクトのタイトル
title_text = "Document-Extraction-Service"

# プロジェクトのバージョン
version_text = "1.0.0"

# プロジェクトの概要
summary_text = "アップロードされた文書ファイルからテキストを抽出する処理を提供します。"

# プロジェクト説明
description_text = """
（詳細な説明を記述）
""".strip()

# APIのタグ情報
tags_metadata = [
    {"name": "テキスト抽出", "description": "アップロードされたドキュメントからテキストを抽出するAPIを提供します。"},
    {"name": "動作確認", "description": "APIサーバーが正常に動作するかを確認します。"},
]

# 参照リンクの情報
contact = {
    "name": "GitHub",
    "url": "https://github.com/takahiro-hirano67/Document-Extraction-Service",
}

# ==========================================
# アプリケーションのインスタンス化
# ==========================================

app = FastAPI(
    title=title_text,  # タイトル
    version=version_text,  # バージョン
    summary=summary_text,  # 概要
    description=description_text,  # 説明
    openapi_tags=tags_metadata,  # APIタグ
    contact=contact,  # 参照リンク
    lifespan=lifespan,  # ライフスパン指定
)

# ==========================================
# CORS設定
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ACCESS_ALLOW_URL],  # 許可する通信元URL
    allow_methods=["POST", "GET"],  # 許可するメソッド
    allow_headers=["*"],  # 許可するリクエストヘッダー
)

# ==========================================
# ルーター登録
# ==========================================

app.include_router(deep_router.router)  # 高精度テキスト抽出API
app.include_router(vision_router.router)  # 高精度テキスト抽出API
# app.include_router(standard_router.router)  # 軽量テキスト抽出API


# ==========================================
# アプリ全体に適用する例外ハンドリング
# ==========================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """アプリケーション全体でキャッチされなかった予期せぬ例外を処理する。

    サーバーには詳細なログを残し、クライアントには安全なメッセージを返す。
    想定内のエラー(ユーザー起因)については各ルーター内で明示的にキャッチ・発生させる。(404など)
    """
    # --- サーバーのログにレベル"ERROR"のスタックトレース（詳細）を出力 ---
    logger.error(
        f"システムエラーが発生しました: {request.method} {request.url}",
        exc_info=True,  # 例外の詳細な発生経路を自動的に連結して出力
    )

    # クライアントには詳細を隠蔽した汎用的なエラーを返す (情報漏洩のリスク回避)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "サーバー内部で予期せぬエラーが発生しました。しばらく経ってから再度お試しください。",
        },
    )


# ==========================================
# 動作確認用エンドポイント
# ==========================================


@app.get("/", tags=["動作確認"])
def read_root() -> dict:
    """ルートページ"""
    return {"document": f"http://localhost:{settings.PORT}/docs"}
