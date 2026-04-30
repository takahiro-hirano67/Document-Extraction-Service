# Makefile

# 環境変数
-include .env
export

# 予約語の回避
.PHONY: format lint

# ==========================================
# サーバー起動
# ==========================================

# FastAPIサーバー起動 (uvicorn)
run:
	uv run uvicorn src.main:app --host 0.0.0.0 --port ${SELF_PORT} --reload

# ==========================================
# Ruff操作
# ==========================================

# コードの自動フォーマット実行
format:
	uv run ruff format .

# フォーマットのチェックのみ
format-check:
	uv run ruff format . --check

# コードの自動修正実行 (※要事前コミット)
lint:
	uv run ruff check . --fix

# 修正箇所のチェックのみ
lint-check:
	uv run ruff check .

# ==========================================
# ヘルプ
# ==========================================

help:
	@echo ""
	@echo "使用可能なコマンド一覧:"
	@echo ""
	@echo "  [Uvicorn] サーバー起動"
	@echo "  make run            FastAPIサーバー起動 (ポート番号: ${SELF_PORT})"
	@echo ""
	@echo "  [Ruff] 静的解析・フォーマット"
	@echo "  make format         コードの自動フォーマット実行"
	@echo "  make format-check   フォーマットのチェックのみ"
	@echo "  make lint           コードの自動修正実行 (※要事前コミット)"
	@echo "  make lint-check     修正箇所のチェックのみ"
	@echo ""
