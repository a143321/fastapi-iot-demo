# システムアーキテクチャ構成図

本プロジェクトのインフラ構成図（Terraformによって構築されたAWSリソースとCI/CDパイプライン）です。


## アーキテクチャ構成図（Mermaid）

```mermaid
graph TD
    %% ユーザーと外部からのリクエスト
    User((ユーザー)) -->|HTTP Request| ALB[Application Load Balancer]
    
    %% CI/CD パイプライン
    Developer((開発者)) -->|Git Push| GitHub[GitHub Repository]
    GitHub -->|Trigger| GHA[GitHub Actions]
    
    GHA -->|1. OIDC Auth| IAM_OIDC[IAM OIDC Provider]
    IAM_OIDC -.->|2. Temp Credentials| GHA
    GHA -->|3. Docker Push| ECR[(Amazon ECR)]
    
    %% AWS クラウド環境
    subgraph AWS Cloud [AWS Cloud - ap-northeast-1]
        
        %% ECR層（基盤）
        ECR
        
        %% アプリ層（VPC内部）
        subgraph VPC [VPC]
            subgraph Public Subnets
                ALB
            end
            
            subgraph Amazon ECS Cluster
                Fargate[Fargate Task\nFastAPI Application]
            end
            
            ALB -->|Routing: Port 80| Fargate
            ECR -.->|4. Image Pull| Fargate
        end
        
        %% データベース・監視層
        DynamoDB[(Amazon DynamoDB\nNoSQL Database)]
        CloudWatch[Amazon CloudWatch\nApplication Logs]
        
        Fargate -->|Read / Write| DynamoDB
        Fargate -->|Put Logs| CloudWatch
    end
    
    %% スタイル定義
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff;
    classDef db fill:#3334B9,stroke:#232F3E,stroke-width:2px,color:#fff;
    classDef compute fill:#D1600F,stroke:#232F3E,stroke-width:2px,color:#fff;
    classDef github fill:#24292e,stroke:#fff,stroke-width:2px,color:#fff;
    classDef user fill:#4CAF50,stroke:#fff,stroke-width:2px,color:#fff;

    class ALB,IAM_OIDC,CloudWatch aws;
    class ECR,DynamoDB db;
    class Fargate compute;
    class GitHub,GHA github;
    class User,Developer user;
```

## アーキテクチャの特長

1. **2層構造（ECRとアプリ基盤の分離）**: 
   図の中央にある `Amazon ECR` と `VPC` 内部のリソースはTerraform上で分離されています。これによりVPC側を破棄してもECRが残り、CI/CDパイプラインを保護します。
2. **完全なサーバーレス（Fargate & DynamoDB）**: 
   EC2サーバーの運用保守が不要な「フルマネージド」なサーバーレスアーキテクチャを採用しており、運用コストとセキュリティリスクを最小化しています。
3. **セキュアなOIDC認証**:
   GitHub ActionsからAWSへのデプロイにはIAMアクセスキーを使用せず、OIDC（OpenID Connect）を利用した一時的な認証情報を利用し、漏洩リスクを根本から防いでいます。
