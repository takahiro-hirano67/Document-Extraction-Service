# src/api/extractors/docx_extractor.py

"""Wordファイル(.docx)からテキストを抽出するモジュール"""

import io
import re
from collections.abc import Iterator

from docx import Document as Open_Docx
from docx.document import Document
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.oxml.xmlchemy import BaseOxmlElement
from docx.table import Table

# ==========================================
# XML名前空間の定義
# ==========================================

# BaseOxmlElement.xpath() は docx.oxml.ns.nsmap を内部で自動適用するため、
# 呼び出し側での名前空間マッピングの指定は不要。
# w: および a: プレフィックスはそのまま XPath 式中で使用可能。

# ==========================================
# パブリック関数
# ==========================================


def extract_from_docx(file_stream: io.BytesIO) -> str:
    """Wordファイルからテキストを抽出する

    抽出順序:
        1. ヘッダー (セクション順)
        2. 本文 (段落・表・図形テキストを出現順に維持)
        3. フッター (セクション順)

    Args:
        file_stream (io.BytesIO): Wordファイルのバイトストリーム

    Returns:
        str: 抽出されたテキスト全文

    """
    document = Open_Docx(file_stream)

    extracted_lines: list[str] = []

    # --- ヘッダーの抽出 (本文より前に付加) ---
    header_lines = _extract_header_text(document)
    if header_lines:
        extracted_lines.extend(header_lines)

    # --- 本文の抽出 (段落・表・図形テキストを出現順に維持) ---
    body_lines = list(_extract_body_text_in_order(document))
    if body_lines:
        extracted_lines.extend(body_lines)

    # --- フッターの抽出 (本文より後に付加) ---
    footer_lines = _extract_footer_text(document)
    if footer_lines:
        extracted_lines.extend(footer_lines)

    # 各行を改行で結合し、連続する空白行を1行に正規化する
    # （2行以上連続する空白行 → 1行の空白行）
    joined_text = "\n".join(extracted_lines)
    normalized_text = re.sub(r"\n{3,}", "\n\n", joined_text)

    return normalized_text


# ==========================================
# プライベート関数: 通常テキストと数式の抽出
# ==========================================


def _extract_text_with_math(element: BaseOxmlElement) -> str:
    """XML要素から通常テキストと数式(OMML)を漏れなく抽出する

    python-docx標準のプロパティ(.text)は数式要素(<m:oMath>)を無視するため、
    XPathを用いて w:t (通常テキスト) と m:t (数式テキスト) を統合して抽出する。
    """
    text_parts: list[str] = []

    tag_w_tab = qn("w:tab")
    tag_w_br = qn("w:br")

    # テキスト、数式、タブ、改行を文書の出現順序で取得
    for node in element.xpath(".//w:t | .//m:t | .//w:tab | .//w:br"):
        if node.tag == tag_w_tab:
            text_parts.append(" ")  # 視認性のためタブはスペース化
        elif node.tag == tag_w_br:
            text_parts.append("\n")  # 明示的な改行タグ
        elif node.text:
            text_parts.append(node.text)

    return "".join(text_parts).strip()


# ==========================================
# プライベート関数: ヘッダー・フッター
# ==========================================


def _extract_header_text(document: Document) -> list[str]:
    """全セクションのヘッダーからテキストを抽出する

    同一テキストのヘッダーが複数セクションで繰り返されるケースが多いため、
    重複を除去しながら抽出する。

    Args:
        document (Document): python-docxのDocumentオブジェクト

    Returns:
        list[str]: ヘッダーから抽出されたテキスト行のリスト

    """
    seen_header_texts: set[str] = set()
    header_lines: list[str] = []

    for section in document.sections:
        for paragraph in section.header.paragraphs:
            # テキストの抽出
            text = _extract_text_with_math(paragraph._p)  # paragraph._p は基礎となるXML要素を表す
            if text and text not in seen_header_texts:
                seen_header_texts.add(text)
                header_lines.append(text)

    return header_lines


def _extract_footer_text(document: Document) -> list[str]:
    """全セクションのフッターからテキストを抽出する

    同一テキストのフッターが複数セクションで繰り返されるケースが多いため、
    重複を除去しながら抽出する。

    Args:
        document (Document): python-docxのDocumentオブジェクト

    Returns:
        list[str]: フッターから抽出されたテキスト行のリスト

    """
    seen_footer_texts: set[str] = set()
    footer_lines: list[str] = []

    for section in document.sections:
        for paragraph in section.footer.paragraphs:
            # テキストの抽出
            text = _extract_text_with_math(paragraph._p)
            if text and text not in seen_footer_texts:
                seen_footer_texts.add(text)
                footer_lines.append(text)

    return footer_lines


# ==========================================
# プライベート関数: 本文 (出現順走査)
# ==========================================


def _extract_body_text_in_order(document: Document) -> Iterator[str]:
    """本文要素を出現順に走査し、テキストを順次 yield する

    body の直接子要素を走査し、段落・表・図形テキストを
    ドキュメント上の出現順序を維持したまま抽出する。

    図形テキスト (w:drawing) は CT_P (段落) の内部に存在するため、
    段落の処理内で同時に抽出することで順序を保証する。

    Args:
        document (Document): python-docxのDocumentオブジェクト

    Yields:
        str: 抽出されたテキスト行

    """
    body_element = getattr(document.element, "body", None)

    # 万が一bodyが存在しない（破損したファイル等）場合は抽出をスキップ
    if body_element is None:
        return

    for child_element in body_element.iterchildren():
        if isinstance(child_element, CT_P):
            # 要素が「段落」の場合:
            # 段落テキストと、段落内の図形テキストをまとめて抽出する
            yield from _extract_paragraph_and_shapes(child_element)

        elif isinstance(child_element, CT_Tbl):
            # 要素が「表」の場合
            table = Table(child_element, document)
            markdown_table = _table_to_markdown(table)
            if markdown_table:
                # 表の前後に見やすくするための空行（\n）を確保する目的で追加
                yield f"\n{markdown_table}\n"


def _extract_paragraph_and_shapes(
    paragraph_element: CT_P,
) -> Iterator[str]:
    """段落要素から本文テキストと図形テキストをまとめて抽出する

    段落内に w:drawing が含まれる場合、テキストボックス・図形テキストも
    この段落の処理内で抽出することで、本文との出現順序を保証する。

    Args:
        paragraph_element (CT_P): 段落のXML要素
        document (Document): python-docxのDocumentオブジェクト

    Yields:
        str: 抽出されたテキスト行

    """
    # 段落の本文テキストを抽出する
    # 空段落（テキストなし）も "" として yield することで、
    # 文書上の空白行をテキスト中に反映させる
    paragraph_text = _extract_text_with_math(paragraph_element)
    has_drawing = bool(paragraph_element.findall(f".//{qn('w:drawing')}"))

    if paragraph_text or not has_drawing:
        # テキストあり: そのまま yield
        # テキストなし かつ 図形なし: 空白行として "" を yield
        yield paragraph_text

    # 段落内に図形 (w:drawing) が存在する場合、図形テキストを抽出する
    # w:drawing は CT_P の内部に含まれるため、ここで処理することで出現順序を保証する
    drawing_elements = paragraph_element.findall(
        f".//{qn('w:drawing')}",
    )
    for drawing_element in drawing_elements:
        yield from _extract_shape_text_from_drawing(drawing_element)


def _extract_shape_text_from_drawing(
    drawing_element: BaseOxmlElement,
) -> Iterator[str]:
    """w:drawing 要素から図形内テキストを抽出する

    対象とする図形テキストのパターン:
        - w:txbxContent: テキストボックス (Wordの「テキストボックス挿入」)
        - a:t: DrawingML図形内テキスト (図形の「テキストを追加」、SmartArt)

    Args:
        drawing_element (BaseOxmlElement): w:drawing のXML要素。
            BaseOxmlElement.xpath() は namespaces 引数不要で Open XML 標準 nsmap を自動適用する。

    Yields:
        str: 抽出されたテキスト行

    """
    # --- テキストボックス (w:txbxContent) ---
    textbox_content_elements = drawing_element.xpath(".//w:txbxContent")
    for txbx in textbox_content_elements:
        text = _extract_text_with_math(txbx)
        if text:
            yield text

    # --- DrawingML図形・SmartArt (a:t) ---
    # ただし、テキストボックス内の a:t は上記で取得済みのため除外する
    # w:txbxContent の外側にある a:t のみを対象とする
    all_drawing_ml_text_elements = drawing_element.xpath(
        ".//a:t",
    )
    textbox_content_elements = drawing_element.xpath(
        ".//w:txbxContent",
    )

    for drawing_ml_text_element in all_drawing_ml_text_elements:
        # このa:tがいずれかのテキストボックス内に含まれているか確認する
        is_inside_textbox = any(
            _is_descendant_of(drawing_ml_text_element, textbox_content_element)
            for textbox_content_element in textbox_content_elements
        )
        if not is_inside_textbox:
            text = (drawing_ml_text_element.text or "").strip()
            if text:
                yield text


def _is_descendant_of(
    target_element: BaseOxmlElement,
    ancestor_element: BaseOxmlElement,
) -> bool:
    """target_element が ancestor_element の子孫であるかを判定する

    Args:
        target_element (BaseOxmlElement): 判定対象の要素
        ancestor_element (BaseOxmlElement): 祖先かどうか確認する要素

    Returns:
        bool: target_element が ancestor_element の子孫であれば True

    """
    current_element = target_element.getparent()
    while current_element is not None:
        if current_element is ancestor_element:
            return True
        current_element = current_element.getparent()
    return False


# ==========================================
# プライベート関数: 表のMarkdown変換
# ==========================================


def _table_to_markdown(table: Table) -> str:
    """python-docxのTableオブジェクトをMarkdownの表形式に変換する

    Args:
        table (Table): python-docxのTableオブジェクト

    Returns:
        str: Markdown形式の表文字列。行が存在しない場合は空文字列を返す。

    """
    if not table.rows:
        return ""

    markdown_lines: list[str] = []

    for row_index, row in enumerate(table.rows):
        # セル内の改行をスペースに置換し、Markdown構文を壊さないようパイプ(|)をエスケープ
        row_cells = [
            _extract_text_with_math(cell._tc).replace("\n", " ").replace("|", "\\|").strip() for cell in row.cells
        ]
        markdown_lines.append("| " + " | ".join(row_cells) + " |")

        # 1行目（ヘッダー）の直後にMarkdownの区切り線を追加
        if row_index == 0:
            separator_cells = ["---"] * len(row.cells)
            markdown_lines.append("| " + " | ".join(separator_cells) + " |")

    return "\n".join(markdown_lines)
