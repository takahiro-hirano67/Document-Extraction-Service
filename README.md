# Document-Extraction-Service

アップロードされた文書ファイルからテキストを抽出する処理を提供します。

## PyTorch で MPS を利用するために必要なライブラリ

`PyTorch` の他に、 `torchvision` もセットでインストールしておく

- `torch`: 多次元配列の計算
- `torchvision`: 画像データの読み込み

## 参考リンク

* [Docling](https://www.docling.ai)
* [Docling GitHub](https://github.com/docling-project/docling)

## ディレクトリ構造 (Project-Treeによる自動出力)


```
Document-Extraction-Service
├─ .python-version
├─ Makefile
├─ README.md
├─ data
│  ├─ __検証用のサンプルデータ配置__
│  ├─ sample_docx_data
│  │  └─ __DOCX形式のサンプル__
│  ├─ sample_patent_pdf_data
│  │  └─ __特許公報PDFのサンプル__
│  ├─ sample_pdf_data
│  │  └─ __PDF形式のサンプル__
│  └─ sample_xlsx_data
│     └─ __XLSX形式のサンプル__
├─ notebooks
│  ├─ 01_テキスト抽出テスト.ipynb
│  └─ __開発検証用ノートブック__
├─ pyproject.toml
├─ repomix.config.json
├─ src
│  ├─ api
│  │  ├─ mode
│  │  │  ├─ __抽出モード別の処理実装__
│  │  │  ├─ deep
│  │  │  │  ├─ __高精度抽出モード__
│  │  │  │  ├─ deep_router.py
│  │  │  │  ├─ services
│  │  │  │  │  └─ deep_service.py
│  │  │  │  └─ utils
│  │  │  │     └─ markdown_cleaner.py
│  │  │  └─ standard
│  │  │     └─ __標準抽出モード__
│  │  └─ shared_modules
│  │     ├─ __共有モジュール__
│  │     └─ schemas
│  │        └─ extract_schema.py
│  ├─ core
│  │  ├─ __環境変数等__
│  │  ├─ config.py
│  │  └─ model_state.py
│  └─ main.py
├─ uv.lock
└─ プロジェクト全体のコード.xml

```