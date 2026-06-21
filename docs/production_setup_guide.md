# 本番環境（AWS）デプロイメントガイド

このドキュメントでは、ゼロからAWS上に本番環境インフラを構築し、アプリケーションをデプロイするまでの完全な手順を説明します。

## 📋 事前準備
* AWS CLI がインストールされ、アクセス権限（AdministratorAccess等）が設定されていること
* Terraform がインストールされていること

## 🚀 デプロイ手順

### 1. インフラの構築（Terraformによる2層アーキテクチャ）
本プロジェクトでは、CI/CDとの競合を防ぐため、インフラを「ECR（共有基盤）」と「アプリ基盤」の2つに分離して構築します。

**① ECR基盤の構築（初回のみ・絶対に破棄しない層）**
基本のIaCアプローチとして、以下のコマンドでECRリポジトリを作成します。
```bash
cd terraform/ecr
terraform init
terraform apply
```
途中で `Enter a value:` と聞かれたら `yes` と入力します。これでDockerイメージの保管庫が完成します。



**② アプリ基盤の構築（何度でも破棄可能な層）**
```bash
cd ../  # terraformディレクトリに戻る
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
（例: `http://prd-fastapi-iot-demo-alb-xxxx.ap-northeast-1.elb.amazonaws.com`）

※もしURLを忘れてしまった場合は、ターミナルで `cd terraform` に移動して `terraform output alb_dns_name` を実行すればいつでも確認できます。

💡 **HTTPアクセスの採用理由と今後の展望**
本プロジェクトはPoC（概念実証）用のデモ環境であるため、AWS ALBが発行するデフォルトのDNS名（`*.elb.amazonaws.com`）をそのまま使用しており、通信プロトコルは `HTTP` となっています。
実運用（本番環境）で `HTTPS` 化を行う場合は、独自ドメイン（Route 53）を取得し、AWS Certificate Manager (ACM) でSSL/TLS証明書を発行してALBにアタッチする設計となります。本デモ環境では検証の手軽さを優先し、HTTPにて稼働させています。

ダークモードのダッシュボード画面が表示されれば、本番環境へのデプロイは100%成功です！

---

## 🗑️ 環境のクリーンアップ（リソースの一括削除）

クラウドの無駄な課金を防ぐため、検証が終わったアプリ環境は以下の手順で完全に削除（クリーンアップ）できます。
ECRをアプリ基盤から分離したアーキテクチャであるため、アプリ側の破棄だけで安全に課金を停止できます。

### アプリ基盤の一括削除（Terraform Destroy）
Terraformディレクトリ（`terraform/`）に移動し、破壊コマンドを実行します。
```bash
cd terraform
terraform destroy
```
途中で `Enter a value:` と聞かれたら `yes` と入力します。
数分待って `Destroy complete!` と表示されれば、高額な課金が発生するAWSリソース（ECS, ロードバランサー, DynamoDB等）はすべて綺麗に削除されます。

💡 **ECRリポジトリについて**
この構成では、ECRリポジトリ（`terraform/ecr/`）は削除されずに残ります。これは次回のCI/CD実行時にエラーを出さないためのベストプラクティスです。Dockerイメージを数個置いているだけのECRストレージ料金は非常に安価（無料枠内または月額数円）なため維持しておくのがおすすめですが、もし完全にすべてを消し去りたい場合は以下のコマンドで強制削除してください。
`aws ecr delete-repository --repository-name prd-fastapi-iot-demo --force`

---

## 💡 トラブルシューティング
Terraform実行時のエラー（例: すでに同名リポジトリが存在する等）や、ECSが起動しないなどの問題が発生した場合は、**[トラブルシューティングガイド](./troubleshooting.md)** に解決策をまとめていますのでご参照ください。
