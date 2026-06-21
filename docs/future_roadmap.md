# System Development Roadmap

本プロジェクト（Smart Home Edge Intelligence）の今後の開発および拡張計画（ロードマップ）です。
現在はコア機能のPoC（概念実証）およびインフラの自動化が完了しており、今後はセキュリティ強化とステートフルなバックエンドへの移行を予定しています。

## 📍 Phase 1: Core API & Deployment (Completed)
- [x] FastAPIとPydanticを用いたIoTデータバリデーション機能の実装
- [x] ダミーAI推論エンドポイントの構築
- [x] ダークモード対応のデモ用ダッシュボードUIの作成
- [x] GitHub ActionsによるCI/CDパイプラインの自動化
- [x] AWS ECS (Fargate) および ECR を用いたパブリックエンドポイントへのデプロイ

## 📍 Phase 2: Infrastructure as Code (Completed)
- [x] AWSコンソール上で手動構築したインフラのTerraformコード化（`terraform/` ディレクトリ）
- [x] ECR, ECS Cluster, IAM RoleのIaC化とドキュメント整備

## 📍 Phase 3: Security & Persistence (Completed)
- [x] **GitHub Actions x AWS OIDC連携**
  - セキュリティのベストプラクティスに基づき、永続的なAWSアクセスキーを廃止。
  - GitHub ActionsからAWSへのデプロイをOpenID Connect (OIDC) による一時クレデンシャルへ移行済み。
- [x] **Amazon DynamoDBによるデータ永続化と可視化**
  - オンメモリで処理していたIoTセンサーデータを、NoSQLデータベース（DynamoDB）に保存・読み出しするステートフルなアーキテクチャへの移行完了。
  - ダッシュボード上に、DynamoDBから取得した時系列データの履歴テーブル（直近10件）と履歴クリア機能を実装。

## 🔮 Phase 4: Authentication & Authorization (Future)
- [ ] **APIキー または JWTベースの認証導入**
  - IoTデバイスから送信されるデータを保護するためのAPIキー認証。
  - ダッシュボードへのアクセスを制限するためのAmazon CognitoまたはJWTによるユーザー認証。

## 🔮 Phase 5: Real-time Communication (Future)
- [ ] **WebSocket連携**
  - FastAPIのWebSocket機能を活用し、IoTデバイスからデータを受信した瞬間に、ブラウザのダッシュボードをリロードなしでリアルタイム更新する仕組みの導入。
