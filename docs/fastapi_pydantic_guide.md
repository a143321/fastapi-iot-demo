# FastAPI & Pydantic ガイド

本ドキュメントは、FastAPIおよびPydanticの主要な機能と、他のフレームワークとの比較についてまとめた技術資料です。

## 1. Webフレームワークの比較

各フレームワークはアーキテクチャの思想や用途が異なります。

| フレームワーク | 特徴 | 適した用途 |
| :--- | :--- | :--- |
| **FastAPI** | API特化・型安全・非同期 | マイクロサービス、IoTバックエンド、AI推論API |
| **Flask** | マイクロフレームワーク | プロトタイプ、小規模アプリ |
| **Django** | フルスタック（全部入り） | 従来型の巨大なWebシステム |

FastAPIは「非同期処理への標準対応」「Pydanticによる自動型チェック」「Swagger仕様書の自動生成」といった特徴から、モダンなAPI開発において強力な選択肢となります。

## 2. 非同期処理 (`async/await`) のメリット
IoTシステムやAIの推論サーバーのように多数のリクエストが来る環境において、非同期処理は非常に有利です。
同期処理では1つのリクエストが完了するまでサーバーのスレッドがブロックされますが、非同期処理であればI/O待ち時間（DBへの保存や外部APIの呼び出しなど）の間に別のリクエストを捌けるため、少ないリソースで大量のアクセスに耐えられます。

## 3. Pydantic (BaseModel) の極意

FastAPIの強さの源泉であるデータバリデーション（型チェック）の仕組みです。

### 基本的な書き方と `Field` の役割
```python
from pydantic import BaseModel, Field

class SensorData(BaseModel):
    # 必須項目（ `...` を指定）で、かつ -273.15 以上という制約を付与
    temperature: float = Field(..., ge=-273.15, description="温度 (℃)")
    
    # 任意項目（初期値を指定）
    occupancy: bool = Field(False, description="在室有無")
```

### Pydanticの実務でのベストプラクティス

#### ① 未知のプロパティを弾くセキュアな設計 (`extra="forbid"`)
デフォルトでは未定義のデータが送られてきても無視してしまいますが、悪意のある通信やデバイスの誤作動を防ぐため、入り口でエラーにする設計が可能です。
```python
from pydantic import ConfigDict

class SensorData(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 未定義のキーを禁止し 422 エラーにする
    temperature: float
```

#### ② リストや辞書の初期値には `default_factory` を使う
Pythonの仕様によるバグ（全ての処理間で同じリストオブジェクトが共有されてしまう）を防ぐため、リストの初期値には空リスト `[]` を直接書かず、`default_factory=list` を使用します。
```python
    tags: list[str] = Field(default_factory=list)
```

#### ③ Pydantic V1 と V2 の違い
最新のPydantic V2はコア部分がRust言語で書き直されており、V1と比べてバリデーション速度が劇的に向上しています。IoTなどの高速処理が求められる環境で非常に有利です。
※V2への移行に伴い、モデルを辞書化するメソッドは `model.dict()` から `model.model_dump()` に推奨が変わっています。
