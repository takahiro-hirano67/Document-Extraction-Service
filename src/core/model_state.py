# src/core/model_state.py

"""モデル状態管理モジュール

Doclingのコンバーターなど、起動時に初期化し、
アプリケーション全体で共有する重いオブジェクトを管理します。
"""

import logging

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import CodeFormulaVlmOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# 処理デバイス
from src.core.config import device

logger = logging.getLogger(__name__)


class ModelState:
    """アプリケーションのグローバル状態を保持するクラス"""

    def __init__(self) -> None:
        """クラスの初期化"""
        self.converter: DocumentConverter | None = None

    def initialize_converter(self) -> None:
        """Doclingのコンバーターを最適なオプションで初期化する"""
        pipeline_options = PdfPipelineOptions()

        # 基本機能の設定
        pipeline_options.do_ocr = False  # OCRの有効化
        pipeline_options.images_scale = 2.0  # OCR処理の前に抽出した画像の解像度を引き上げる(2倍)
        pipeline_options.do_table_structure = True  # テーブル解析の有効化
        pipeline_options.do_formula_enrichment = True  # 数式解析の有効化

        # --- 1. アクセラレータの動的設定 ---
        device_str = str(device).upper()  # 大文字に変換
        pipeline_options.accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice[device_str],  # "MPS", "CUDA", "CPU" のいずれかが設定される
        )

        # --- 2. デバイス(MPS)に応じたエンジン最適化 ---
        if device_str == "MPS":
            try:
                # 実行時インポートで、Mac以外の環境での ImportError を防ぐ
                from docling.datamodel.vlm_engine_options import MlxVlmEngineOptions

                formula_options = CodeFormulaVlmOptions.from_preset("codeformulav2")
                formula_options.engine_options = MlxVlmEngineOptions()
                pipeline_options.code_formula_options = formula_options

                logger.info("Apple Silicon(MPS)向けのMLXエンジン最適化を適用しました。")
            except ImportError:
                logger.warning("MLX関連のライブラリが見つかりません。デフォルトのエンジンにフォールバックします。")
        else:
            # CUDA や CPU の場合は、Docling標準の自動判定（Transformers等）に任せる...(必要に応じて追加実装)
            logger.info(f"{device_str}向けのデフォルトエンジン（Transformers等）を使用します。")

        # --- 3. コンバーターの初期化 ---
        # サポートする形式をリストで指定
        allowed_formats = [
            InputFormat.PDF,
            InputFormat.DOCX,
            InputFormat.XLSX,
            InputFormat.PPTX,
            InputFormat.HTML,
            InputFormat.MD,
            InputFormat.CSV,
        ]

        self.converter = DocumentConverter(
            allowed_formats=allowed_formats,
            format_options={
                # PDFの時だけ、これまで設定した重いパイプライン（OCRやMLXエンジン）を適用
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            },
        )


# グローバルにアクセス可能なインスタンス
model_state = ModelState()
