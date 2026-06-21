# Infrastructure as Code (IaC) - Terraform Guide

本プロジェクトでは、AWSインフラストラクチャの構築と管理に **Terraform** を採用（想定）しています。

現在稼働中のデモ環境（パブリックURL）はプロトタイプとしてAWSコンソール（ECS Express Mode）から手動で構築されていますが、**実務環境や複数環境（Dev/Staging/Prod）への横展開を想定**し、インフラのあるべき姿をIaC（Infrastructure as Code）としてコード化し、バージョン管理しています。

## 📂 ディレクトリ構成 (`/terraform`)

```text
terraform/
├── main.tf         # AWSリソースの定義（ECR, ECSクラスター, IAMロールなど）
├── variables.tf    # 変数の定義（リージョン, プロジェクト名など）
└── providers.tf    # TerraformおよびAWSプロバイダーのバージョン指定
```

## 🏗 定義されている主要なリソース

1. **Amazon ECR (Elastic Container Registry)**
   - Dockerイメージの保存先。
   - `image_scanning_configuration` を有効化し、Push時の脆弱性スキャンを自動実行するセキュアな設計としています。
2. **Amazon ECS (Elastic Container Service)**
   - フルマネージドなコンテナ実行環境用のクラスター。
   - Container Insightsを有効化し、詳細なメトリクス監視を行えるように設定しています。
3. **AWS IAM Roles**
   - ECSタスク実行ロール（`ecsTaskExecutionRole` 相当）を定義。
   - コンテナがAWSリソース（ログの書き出しやECRからのイメージPull）にアクセスするための「最小権限の原則」を適用したロールです。
4. **Amazon CloudWatch Log Group**
   - アプリケーションログの出力先。ログの保持期間（30日）を明示的に指定しています。

*(※注: ECSの「サービス」や「ALB」の定義は、Express Modeと同等の構成を再現するためにVPC構築から記述する必要がありますが、本プロジェクトではコアコンポーネントのみを抽出して定義しています)*

## 🚀 使い方（実務想定）

実務においてこのインフラを展開する場合は、以下のTerraformコマンドを実行します。

```bash
cd terraform

# 1. プラグインの初期化
terraform init

# 2. 変更内容の事前確認（レビュー用）
terraform plan

# 3. AWSへのデプロイ実行
terraform apply
```

## 🛡 なぜIaC (Terraform) が必要なのか？

面接や実務において、Terraformを導入するメリットは以下の通りです。

1. **属人化の排除と再現性の担保**
   - 「誰がAWSの画面のどこをクリックしたか」というブラックボックスをなくし、コマンド1つで全く同じ環境（ステージング環境など）を何度でも正確に複製できます。
2. **レビュー可能なインフラ（Pull Request）**
   - インフラの変更がコードとして表現されるため、アプリケーションコードと同様にGitHub上でピアレビューを行うことができます。
3. **継続的インテグレーション（CI/CD）との親和性**
   - GitHub Actionsと組み合わせることで、「`main`ブランチにマージされたら自動でインフラもアップデートする」といった高度な自動化（GitOps）が可能になります。
