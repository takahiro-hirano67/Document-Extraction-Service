# Document-Extraction-Service

メインサーバーから独立して稼働する、ドキュメント・画像からのテキスト抽出専用APIサービスです。FastAPIをベースに構築されています。

## 本サービスを独立させた理由

本リポジトリは、以下の目的でメインのアプリケーションから分離・独立したサブリポジトリとして設計されています。

1. **重厚な依存関係の隔離**: 高度なPDF解析を行う `Docling` や画像解析のローカルAI等の重い依存ライブラリを切り離し、メインリポジトリの肥大化を防ぐため。
2. **関心の分離**: ファイル形式（PDF, DOCX, XLSX, PPTX, 画像等）ごとに異なる複雑な抽出ロジック・クリーニング処理を一つのリポジトリに集約・隠蔽するため。
3. **Apple Silicon (MPS) のフル活用**: Dockerコンテナを経由せず、ホストOS（Mac）上で直接サーバーを起動することで、Apple SiliconのGPUアクセラレーション (MPS) を用いた高速な推論・解析処理（DoclingのMLXエンジン等）を可能にするため。

## 主な機能と対応フォーマット

アップロードされたファイルからテキストをメモリ上で高速に抽出し、構造化されたテキストとして返却します。

- **PDF (`.pdf`)**: Doclingを利用した高精度なテキスト・構造抽出（テキストレイヤーがあるもの）
- **Word (`.docx`)**: 本文、表、ヘッダー、フッター、図形内テキスト（テキストボックス、DrawingML図形）
- **Excel (`.xlsx`)**: 全シートのセルデータ（計算後の値）、図形・テキストボックス内のテキスト（CSVライクなカンマ区切りで出力）
- **PowerPoint (`.pptx`)**: 全スライドのテキスト、グループ化図形内テキスト、表、スライドノート
- **画像 (`.png`, `.jpg`, `.jpeg`)**: Ollama (VLM: 視覚言語モデル) を用いた画像からのテキスト認識（GLM-OCR等を使用）
- **テキスト (`.txt`, `.md`)**: 文字コードを自動判定して読み込み

## 前提条件

- **Python**: 3.14 以上
- **パッケージマネージャー**: [uv](https://github.com/astral-sh/uv)
- **画像抽出機能を利用する場合**: [Ollama](https://ollama.com/) がホストマシン上で稼働していること
    - 推奨モデル: `glm-ocr`

## セットアップ手順

1. **リポジトリのクローンとディレクトリ移動**

```bash
git clone <repository-url>
cd Document-Extraction-Service

```

2. **依存関係のインストール**

`uv` を使用して依存パッケージをインストールします。Mac環境の場合は自動的に最適化されたMLX関連パッケージがインストールされます。

```bash
uv sync
```

3. **環境変数の設定**

`.env.example` をコピーして `.env` ファイルを作成し、ご自身の環境に合わせて設定してください。

```bash
cp .env.example .env
```

_主な設定項目:_

- `SELF_PORT`: 本APIサーバーが起動するポート (デフォルト: 8001)
- `ACCESS_ALLOW_URL`: リクエストを許可するメインサーバーのURL
- `OLLAMA_URL`: OllamaのAPIエンドポイント (例: `http://localhost:11434`)

4. **(オプション) 画像解析用モデルの準備**

画像抽出を行う場合は、OllamaでモデルをPullしておきます。

```bash
ollama run glm-ocr
```

## 起動と操作

開発・実行には `Makefile` に定義されたコマンドを利用します。

**サーバーの起動:**

```bash
make run
```

※ 起動後、APIドキュメントは `http://localhost:<SELF_PORT>/docs` で確認できます。

## API仕様

### エンドポイント

`POST /extract/text`

アップロードされたドキュメントや画像からテキストを抽出します。

**Request (multipart/form-data):**

- `file`: 抽出対象のファイル (PDF, DOCX, XLSX, PPTX, 画像, TXT, MD)

**Response (JSON):**

```json
{
    "status": "success",
    "filename": "document.pdf",
    "file_type": "pdf",
    "extracted_text": "抽出されたテキストの全文がここに入ります..."
}
```

_※セキュリティ対策として、拡張子の偽装検知（マジックナンバー検証）や、OfficeファイルのZip Bomb（メモリ枯渇攻撃）対策が組み込まれています。_

## ディレクトリ構造

```text
Document-Extraction-Service
├─ .python-version
├─ Makefile
├─ README.md
├─ pyproject.toml
├─ src
│  ├─ api
│  │  ├─ cleaners/       # 抽出後のテキスト整形ロジック (特許固有の処理など)
│  │  ├─ extractors/     # ファイル形式別の抽出ロジック (PDF, DOCX, XLSX, PPTX, Image)
│  │  ├─ schemas/        # リクエスト/レスポンスの型定義
│  │  ├─ services/       # 抽出処理の統合ロジック
│  │  ├─ utils/          # セキュリティ検証等のユーティリティ
│  │  └─ extract_router.py # APIエンドポイント定義
│  ├─ core
│  │  ├─ config.py       # 環境変数・デバイス(MPS)判定
│  │  └─ model_state.py  # Docling等の重いインスタンスのライフサイクル管理
│  └─ main.py            # FastAPIアプリケーションのエントリーポイント
└─ uv.lock
```

## 参考リンク

- [Docling](https://www.docling.ai) / [GitHub](https://github.com/docling-project/docling)
- [Ollama](https://ollama.com/)
- [Apple MLX](https://github.com/ml-explore/mlx)
