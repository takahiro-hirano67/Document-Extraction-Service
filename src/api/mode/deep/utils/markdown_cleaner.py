# src/api/mode/deep/utils/markdown_cleaner.py

"""テキスト整形モジュール"""

import re


def clean_markdown(content: str) -> str:
    """抽出されたMarkdownテキストを、LLMやフロントエンドが解釈しやすい形に正規化する

    Args:
        content (str): Doclingから出力された生のMarkdownテキスト

    Returns:
        str: 正規化されたMarkdownテキスト

    """
    if not content:
        return ""

    processed_content = content

    # 1. 数式デリミタの正規化
    # Doclingが出力する \[ ... \] や \( ... \) を $$...$$ や $...$ に変換
    processed_content = re.sub(r"\\\[([\s\S]*?)\\\]", r"$$\1$$", processed_content)
    processed_content = re.sub(r"\\\(([\s\S]*?)\\\)", r"$\1$", processed_content)

    # 2. KaTeX Aligned Fix (数式の描画エラー防止)
    # 数式内に '&' (整列) があり、かつ環境指定(\begin)がない場合、自動的に aligned 環境で囲む
    def align_replacer(match: re.Match) -> str:
        equation = match.group(1)
        # 既に環境指定(\begin)がある場合は何もしない
        if "\\begin" in equation:
            return match.group(0)

        # '&' (整列タブ) が含まれている場合、補正対象とする
        if "&" in equation:
            return f"$$\n\\begin{{aligned}}\n{equation}\n\\end{{aligned}}\n$$"

        return match.group(0)

    processed_content = re.sub(r"\$\$([\s\S]*?)\$\$", align_replacer, processed_content)

    # 3. コードブロックの正規化
    # コードブロックの ``` の直前に改行がないと正しくパースされない場合への対処
    processed_content = re.sub(r"([^\n])```", r"\1\n```", processed_content)

    return processed_content
