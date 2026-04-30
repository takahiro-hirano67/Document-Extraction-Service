# src/api/utils/text_cleaner.py

"""テキスト整形モジュール"""

import re
import unicodedata

from .patent_cleaner import clean_patent_text

PATENT_PATTERN = r"【[^】]*請求項\d*[^】]*】"


def normalize_text(text: str) -> str:
    """テキストを正規化する"""
    text = unicodedata.normalize("NFKC", text)
    return text


def clean_docling_markdown(text: str) -> str:
    """抽出されたMarkdownテキストを、LLMやフロントエンドが解釈しやすい形に整形する

    Args:
        text (str): Doclingから出力された生のMarkdownテキスト

    Returns:
        str: 整形されたMarkdownテキスト

    """
    # テキストの正規化
    text = normalize_text(text)
    # 日本語間スペース除去 (ASCII以外＝日本語ほぼ全て)
    text = re.sub(r"(?<=[^\x00-\x7F]) (?=[^\x00-\x7F])", "", text)
    if re.search(PATENT_PATTERN, text):
        """特許公報だった場合の整形処理"""
        text = clean_patent_text(text)
    # 3つ以上の空行を2つにまとめる - 改行数の調整
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
