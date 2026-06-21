# トラブルシューティングガイド

本プロジェクトの開発および運用中に発生した主要なトラブルと、その解決策（ベストプラクティス）を記録します。
このドキュメントは、インフラ構築時やCI/CD運用時における「クラウド特有の罠」を回避するための知見集です。

---

## 1. ECSデプロイに関するトラブル

### 🚨 症状: コードを修正してPushし、ECSで「強制デプロイ」したのに反映されない
* **詳細**: GitHub Actionsで正常に新しいイメージがビルド・Pushされた後、ECSのサービス更新画面で「強制的に新しいデプロイ」にチェックを入れて更新した。しかし、1分も経たずにデプロイが完了し、動作確認すると古いコードのまま動いている。
* **原因**: ECSの「タスク定義（イメージURI）」の仕様によるトラップ。
  デプロイ時、ECSは安定稼働のために `latest` タグをその時点の一意なハッシュ値（例: `@sha256:29505ae...`）に変換して固定する。次回の更新時、この固定されたURIのまま「強制デプロイ」を実行すると、AWSは「固定された古いイメージ」を再度引っ張ってきてコンテナを再起動してしまう。
* **解決策**:
  1. ECSの「サービスを更新」画面を開く。
  2. 「イメージ URI」の入力欄を確認し、末尾の `@sha256:...` をすべて削除する。
  3. 代わりに `:latest` と手動で書き換える。（例: `.../fastapi-iot-demo:latest`）
  4. その状態で「強制的に新しいデプロイ」にチェックを入れて更新する。

---

## 2. アプリケーション設計に関するトラブル

### 🚨 症状: APIは `200 OK` を返すが、DynamoDBにデータが保存されていない
* **詳細**: API（Swagger UIなど）からPOSTリクエストを送信すると成功レスポンスが返ってくるが、DynamoDBのコンソールを見るとテーブルが空のままになっている。
* **原因**: コード内の不適切なエラーハンドリング（エラー握りつぶし）。
  DynamoDBの書き込み処理を `try...except` で囲み、エラーが発生しても単に `print` するだけで処理を継続させていた。結果として、権限エラー等で書き込みに失敗しても正常ルートとして `200 OK` が返却されてしまっていた。
* **解決策**:
  エラー発生時に例外を握りつぶさず、必ずクラッシュさせるか明示的なエラーレスポンスを返すように修正する。
  ```python
  except Exception as e:
      import traceback
      error_details = f"DynamoDB Error: {str(e)}\n{traceback.format_exc()}"
      print(f"=== ERROR LOG ===\n{error_details}\n=================") # CloudWatch詳細ログ用
      raise HTTPException(status_code=500, detail=f"保存に失敗: {str(e)}") # クライアント用
  ```

---

## 3. CI/CD（自動テスト）に関するトラブル

### 🚨 症状: ローカルで成功する自動テストが、GitHub Actions上で `NoCredentialsError` で落ちる
* **詳細**: アプリにDynamoDBへの書き込み処理を追加した直後から、GitHub Actionsの `pytest` ステップがエラーで強制終了するようになった。
* **原因**: 権限の不在。
  GitHub Actionsのテストランナー（環境）にはAWSのクレデンシャル（アクセス権限）が付与されていないため、テスト環境がマジメにAWS（DynamoDB）へ通信しようとして認証エラーで弾かれてしまう。
* **解決策**:
  `unittest.mock.patch` を使用して、テスト実行時のみAWS呼び出し部分を「モック（ダミー）」にすり替える。
  ```python
  # test_main.py の設定例
  import pytest
  from unittest.mock import patch

  @pytest.fixture(autouse=True)
  def mock_dynamodb():
      """CI/CD環境でAWS認証エラーが出ないようにDynamoDBをモック化"""
      with patch("main.dynamodb.Table") as mock_table:
          yield mock_table
  ```

---

## 4. IAM（権限）に関するトラブル

### 🚨 症状: ECS上でコンテナが `NoCredentialsError` や `AccessDenied` でクラッシュする
* **詳細**: ECS上で動くコンテナがAWSサービス（DynamoDBなど）にアクセスしようとした瞬間に権限エラーが発生する。
* **原因**: 「タスクロール」と「タスク実行ロール」の混同。
  * **タスク実行ロール（Task Execution Role）**: ECSの裏方（エージェント）が、ECRからイメージをPullしたり、CloudWatchにログを送信したりするための権限。
  * **タスクロール（Task Role）**: **コンテナの中で動くアプリそのもの（今回のPythonコード）** が、AWSの他サービス（DynamoDBやS3など）にアクセスするための権限。
  「タスク実行ロール」にDynamoDBの権限を付与しても、アプリ自体はアクセスできない。
* **解決策**:
  アプリ用のIAMロール（例: `fastapi-iot-demo-task-role`）を作成し、そこに `AmazonDynamoDBFullAccess` などのポリシーをアタッチした上で、ECSタスク定義の **「タスクロール（Task Role）」** にそのロールを割り当てる。

---

## 5. Terraform（インフラ構築）に関するトラブル

### 🚨 症状: Terraform実行時に `RepositoryAlreadyExistsException` エラーで失敗する
* **詳細**: `terraform apply` 実行時に、ECRリポジトリ作成フェーズで以下のエラーが表示され、デプロイが強制終了する。
  `RepositoryAlreadyExistsException: The repository with name 'xxx' already exists in the registry...`
* **原因**: TerraformのState（状態）ファイルの不整合。
  手動作成や過去のテストなどによって、**すでにAWS上に同名のリソース（ECRリポジトリ等）が存在している**が、Terraformの現在のStateファイル（`terraform.tfstate`）にはその情報が記録されていないため、Terraformが「新規作成」しようとして競合（名前衝突）が発生している。
* **解決策**:
  以下のいずれかの方法で解消する。
  1. **既存リソースをTerraform管理下に取り込む（推奨）**:
     `terraform import` コマンドを使用して、既存のAWSリソースをStateファイルにインポートする。
     ```bash
     terraform import aws_ecr_repository.app_repo <リポジトリ名>
     ```
  2. **既存リソースを削除して再作成する（テスト用環境の場合）**:
     中身が消えても問題ないリソースであれば、AWSコンソールやCLIから手動で削除してから、再度Terraformを実行する。
     ```bash
     aws ecr delete-repository --repository-name <リポジトリ名> --force
     terraform apply
     ```
