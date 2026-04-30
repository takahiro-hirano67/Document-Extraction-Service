# Document-Extraction-Service

アップロードされた文書ファイルからテキストを抽出する処理を提供します。

## 参考リンク

- [Docling](https://www.docling.ai)
- [Docling GitHub](https://github.com/docling-project/docling)

## ディレクトリ構造

`Project-Tree`による自動出力:

```
Document-Extraction-Service
├─ .python-version
├─ Makefile
├─ README.md
├─ data
│  ├─ __検証用のサンプルデータ配置__
│  ├─ sample_docx_data
│  ├─ sample_img_data
│  ├─ sample_patent_pdf_data
│  ├─ sample_pdf_data
│  ├─ sample_pptx_data
│  └─ sample_xlsx_data
├─ notebooks
│  ├─ 01_テキスト抽出テスト.ipynb
│  └─ __開発検証用ノートブック__
├─ pyproject.toml
├─ repomix.config.json
├─ src
│  ├─ api
│  │  ├─ extract_router.py
│  │  ├─ extractors
│  │  │  ├─ docx_extractor.py
│  │  │  ├─ image_extractor.py
│  │  │  ├─ pdf_extractor.py
│  │  │  ├─ pdf_extractor_docling.py
│  │  │  ├─ pptx_extractor.py
│  │  │  ├─ text_extractor.py
│  │  │  └─ xlsx_extractor.py
│  │  ├─ schemas
│  │  │  └─ extract_schema.py
│  │  ├─ services
│  │  │  └─ extract_service.py
│  │  └─ utils
│  │     └─ text_cleaner.py
│  ├─ core
│  │  ├─ __環境変数等__
│  │  ├─ config.py
│  │  └─ model_state.py
│  └─ main.py
├─ uv.lock
└─ プロジェクト全体のコード.xml

```
