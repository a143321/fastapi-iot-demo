# 本番環境（AWS）デプロイメントガイド

このドキュメントでは、ゼロからAWS上に本番環境インフラを構築し、アプリケーションをデプロイするまでの完全な手順を説明します。

## 📋 事前準備
* AWS CLI がインストールされ、アクセス権限（AdministratorAccess等）が設定されていること
* Terraform がインストールされていること

## 🚀 デプロイ手順

### 1. インフラの構築（Terraform）
まず、アプリケーションを動かすためのインフラ（ECR, ECS, DynamoDB, ロードバランサーなど）をAWS上に一括で作成します。

```bash
cd terraform
terraform init
terraform plan
terraform apply
```
途中で `Enter a value:` と聞かれたら `yes` と入力します。
完了すると、ターミナルにロードバランサーのURL（`alb_dns_name`）が出力されるのでメモしておきます。

### 2. GitHub Actions用 OIDC連携の設定
「GitHub ActionsがAWSリソースを操作するための権限（IAMロール）」を作成します。（※初回の1度だけ必要です）
詳細は [OIDCマイグレーションガイド](./oidc_migration_guide.md) を参照してください。

### 3. アプリケーションのデプロイ（CI/CD）
インフラの準備が整ったら、アプリケーションのコードをGitHubにPushします。

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```
このPushをトリガーとして、GitHub Actionsが自動的に起動します。「テスト → Dockerビルド → AWS ECRへのイメージPush」のすべてが全自動で実行されます。GitHubの **Actions** タブで進行状況を確認できます。

### 4. 動作確認
GitHub Actionsの処理がすべて「Success」になったら、手順1で出力されたロードバランサーのURLにブラウザでアクセスします。
（例: `http://fastapi-iot-demo-alb-xxxx.ap-northeast-1.elb.amazonaws.com`）

ダークモードのダッシュボード画面が表示されれば、本番環境へのデプロイは100%成功です！

---

## 🗑️ 環境のクリーンアップ（リソースの一括削除）

クラウドの無駄な課金を防ぐため、検証が終わった環境は以下の手順で完全に削除（クリーンアップ）できます。
GitHub ActionsによってECRにDockerイメージが保存されているため、**「①ECRリポジトリの強制削除」→「②Terraformによるインフラ一括破棄」** の2ステップで行います。

### 1. ECRリポジトリの強制削除
手元のターミナルで以下のコマンドを実行し、中身のイメージごとリポジトリを削除します。
```bash
aws ecr delete-repository --repository-name fastapi-iot-demo --force
```

### 2. インフラの一括削除（Terraform Destroy）
Terraformディレクトリに移動し、破壊コマンドを実行します。
```bash
cd terraform
terraform destroy
```
途中で `Enter a value:` と聞かれたら `yes` と入力します。
数分待って `Destroy complete!` と表示されれば、今回作成したAWSリソース（ECS, DynamoDB, ロードバランサー, IAM等）はすべて綺麗に削除され、これ以上の課金は発生しません。

（※再度構築したい場合は、もう一度 `terraform apply` を実行するだけで全く同じ環境が蘇ります！）

---

## 💡 トラブルシューティング
Terraform実行時のエラー（例: すでに同名リポジトリが存在する等）や、ECSが起動しないなどの問題が発生した場合は、**[トラブルシューティングガイド](./troubleshooting.md)** に解決策をまとめていますのでご参照ください。
