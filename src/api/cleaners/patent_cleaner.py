# src/api/utils/patent_cleaner.py

"""特許公報テキストの整形モジュール"""

import re


def clean_patent_text(text: str) -> str:
    """PDFから抽出された特許公報テキストを、LLMやフロントエンドが解釈しやすい形に整形する

    Args:
        text (str): 特許公報テキスト

    Returns:
        str: 整形されたMarkdownテキスト

    """
    text = _patent_initial_layout_cleaner(text)
    text = _patent_hedding_line_cleaner(text)
    text = _patent_hedding_line_adjaster(text)
    return text


def _patent_initial_layout_cleaner(text: str) -> str:
    # --- 特許公報PDF特有のレイアウトを除去 ---
    header_line_pattern = r"JP[\s\xa0]+\d+[\s\xa0]+[A-Z]\d*[\s\xa0]+\d{4}\.\d{1,2}\.\d{1,2}"
    text = re.sub(r"̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶̶", "", text)  # 区切り線を除去
    text = re.sub(r"フロントページの続き.*", "", text, flags=re.DOTALL)  # 該当テキスト以降を全て除去
    text = re.sub(header_line_pattern, "", text)  # ヘッダーの文書番号を除去
    text = re.sub(r"\(\d+\)", "", text)  # (50)のような表記を除去
    text = re.sub(r"(?m)^\d+\s*$", "", text, flags=re.MULTILINE)  # 行番号除去 例)10\n20\n30\n40\n50
    # --- Doclingによる抽出特有のテキストを除去 ---
    text = re.sub(r"```", "", text)  # コードブロックを除去
    text = re.sub(r"<!-- image -->", "", text)  # 画像の位置表示を除去
    # --- 改行調整 ---
    text = re.sub(r"。", "。\n", text)  # `。`の後に改行を挿入
    return text


def _patent_hedding_line_cleaner(text: str) -> str:
    cleaned_lines = []

    for line in text.splitlines():
        if "【" in line and "】" in line:
            # 行頭の # や - とそれに続くスペースを削除
            line = line.lstrip(" #-")
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _patent_hedding_line_adjaster(text: str) -> str:
    text = re.sub(r"(?m)^【", "\n\n【", text)  # 【見出し】の前に改行を挿入
    text = re.sub(r"】$", "】\n\n", text, flags=re.MULTILINE)  # 【見出し】の後に改行を挿入
    text = re.sub(r"\n{3,}", "\n\n", text)  # 3つ以上の空行を2つにまとめる (改行数の調整)
    return text
