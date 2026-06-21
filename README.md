# 🚀 Smart Home Edge Intelligence - FastAPI IoT & AI Demo

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.4-009688.svg)
![AWS ECS](https://img.shields.io/badge/AWS-ECS%20Fargate-FF9900.svg)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF.svg)

架空の「スマートホーム向けエッジAIデバイス」を想定した、IoTセンサーデータの収集および異常検知（ダミー推論）を行うバックエンドAPIシステムです。

単なるアプリケーションの開発にとどまらず、**「実務を想定したインフラ構築とCI/CDパイプラインの自動化」** に重点を置いて設計・実装しています。

## 🌟 アピールポイント（実務想定の設計）

1. **GitHub Actionsによる完全自動CDパイプライン**
   - コードを `main` ブランチにPushするだけで、自動的に `pytest` による単体テストが実行されます。
   - テスト成功時のみDockerイメージがビルドされ、AWS ECRに自動プッシュされます。
2. **AWS ECS (Fargate) によるコンテナ運用とIAM設計 (OIDC連携)**
   - フルマネージドなコンテナ環境（ECS Express Mode）を採用し、スケーラビリティを確保。
   - CI/CDパイプラインにはセキュリティベストプラクティスである「OIDC (OpenID Connect)」を採用し、永続的なアクセスキーを廃止したセキュアな設計を行っています。詳細は [OIDCマイグレーションガイド](./docs/oidc_migration_guide.md) を参照。
3. **Pydanticによる堅牢なデータバリデーション**
   - IoTデバイスから送信されるJSONデータ（温度、湿度、モーションセンサー等）の型チェックと制約を厳密に定義し、不正なデータの混入をAPIの入り口で防ぎます。
4. **Terraformによるインフラのコード化 (IaC)**
   - 再現性の確保と属人化の排除のため、本番運用のインフラストラクチャをTerraformでコード化しています。
   - ※詳細は [IaC / Terraform ガイド](./docs/iac_terraform_guide.md) および `terraform/` ディレクトリを参照。
5. **継続的な拡張を前提としたロードマップ**
   - 単なるPoCにとどまらず、OIDC連携によるセキュリティ強化やDynamoDBによるデータ永続化など、実務を見据えた拡張を段階的に実施しています。
   - ※詳細は [今後のロードマップ](./docs/future_roadmap.md) を参照。

## 📸 システム稼働エビデンス（本番環境）

### 1. CI/CD パイプライン（GitHub Actions）
Pushをトリガーに自動テストとコンテナビルドが行われ、ECRへデプロイされる全自動パイプラインです。
![CI/CD Pipeline](./assets/prd_01_cicd_github_actions.png)

### 2. IoTダッシュボード稼働画面（フロントエンド）
AWS ALB経由で配信されているダークモードのデモ用UIです。
![IoT Dashboard](./assets/prd_02_frontend_alb_dashboard.png)

### 3. API仕様とルーティング（Swagger UI）
FastAPIによって自動生成される、OpenAPI準拠のインタラクティブなAPIドキュメントです。
![Swagger UI](./assets/prd_03_backend_swagger_api.png)

### 4. データベースのデータ永続化（DynamoDB）
IoTデバイスから送信されたデータが、権限設定に基づきセキュアにDynamoDBへ書き込まれています。
![DynamoDB](./assets/prd_04_database_dynamodb_items.png)

### 5. コンテナインフラ稼働状況（Amazon ECS Fargate）
サーバーレスコンテナ基盤（Fargate）上で、アプリケーションが正常にアクティブ状態で稼働しています。
![AWS ECS](./assets/prd_05_infra_ecs_fargate.png)

---

## 🏗 システムアーキテクチャ

以下の図は、本プロジェクトの継続的インテグレーション・デプロイ（CI/CD）およびクラウドインフラの全体像を示しています。

```mermaid
graph LR
    subgraph Local [ローカル開発環境]
        Dev[開発者] -->|1. git push| Git[GitHub Repository]
    end

    subgraph CI_CD [GitHub Actions]
        Git -->|2. Trigger Workflow| Test[Pytest]
        Test -->|3. Success| Build[Docker Build]
        Build -->|4. Push Image| ECR_Auth[AWS IAM Auth]
    end

    subgraph AWS_Cloud [AWS Cloud]
        ECR_Auth -->|5. Store Image| ECR[(Amazon ECR)]
        ECR -.->|6. Pull Image| ECS[Amazon ECS<br>Express Mode]
        ECS -->|7. Expose| ALB[Load Balancer]
    end

    User[Web/IoT Client] -->|8. HTTP Request| ALB
```

## 🛠 技術スタック

- **Backend Framework**: Python, FastAPI, Pydantic
- **Testing**: Pytest, httpx
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Cloud Infrastructure**: Amazon Web Services (AWS)
  - Amazon ECR (Elastic Container Registry)
  - Amazon ECS (Elastic Container Service / Express Mode)
  - AWS IAM (Identity and Access Management)
  - Terraform (Infrastructure as Code)
- **Frontend (Demo)**: HTML5, Vanilla CSS, JavaScript

## 📚 ドキュメントと使い方

プロジェクトの詳細なセットアップ方法や運用ルールについては、以下の専用ドキュメントをご用意しています。用途に合わせてご参照ください。

### 💻 ローカルでの開発・テスト
データベース（DynamoDB）を含めた環境を手元で簡単に立ち上げる手順です。
👉 **[ローカル開発・テスト環境ガイド](./docs/local_development_guide.md)** 

```bash
# Docker Composeで一括起動
docker compose up -d

# ブラウザで以下のURLにアクセス
# デモUI: http://localhost:8000/
# DB確認: http://localhost:8002/
```

### ☁️ AWS本番環境へのデプロイ
Terraformを用いたインフラの自動構築から、GitHub ActionsによるCI/CDデプロイまでの完全な手順です。
👉 **[本番環境デプロイメントガイド](./docs/production_setup_guide.md)** 

### 🔧 その他技術資料
* **[Terraform / IaC アーキテクチャ解説](./docs/iac_terraform_guide.md)**
* **[OIDC (OpenID Connect) 連携ガイド](./docs/oidc_migration_guide.md)**
* **[トラブルシューティング集](./docs/troubleshooting.md)**
