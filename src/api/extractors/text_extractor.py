# src/api/extractors/text_extractor.py

"""テキストファイルからテキストを抽出するモジュール"""


def extract_from_text(content: bytes) -> str:
    """テキストファイルからテキストを抽出する"""
    try:
        # テキストファイルとしてデコード
        return content.decode("utf-8")
    except UnicodeDecodeError:
        # UTF-8で読めない場合のフォールバック
        return content.decode("shift_jis", errors="ignore")
