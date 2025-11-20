# Kong API Gateway を使用した Spring PetClinic on Kubernetes

Spring PetClinic マイクロサービスアプリケーションのクラウドネイティブ実装です。API 管理に Kong API Gateway を使用し、Kubernetes (k3s) 上にデプロイします。

> **⚠️ 重要な注意事項**
> 
> このプロジェクトのコードは **Cursor AI** によって生成されました。
> - すべてのKubernetesマニフェスト、デプロイメントスクリプト、設定ファイルはAIによって自動生成されています
> - 予期しない動作や設定ミスが含まれる可能性があります
> - 本番環境で使用する前に、すべての設定を十分に検証してください
> - このプロジェクトはデモンストレーション目的であり、本番環境での使用は推奨されません

## 📋 目次

- [オリジナルからのカスタマイズ](#オリジナルからのカスタマイズ)
- [アーキテクチャ](#アーキテクチャ)
- [前提条件](#前提条件)
- [クイックスタート](#クイックスタート)
- [API エンドポイント](#api-エンドポイント)
- [GenAI Python Service](#genai-python-service)
- [デプロイの詳細](#デプロイの詳細)
- [Kong Gateway 設定](#kong-gateway-設定)
- [監視と可観測性](#監視と可観測性)
- [トラブルシューティング](#トラブルシューティング)
- [クリーンアップ](#クリーンアップ)

## 🔄 オリジナルからのカスタマイズ

このプロジェクトは、[Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices)をベースに、以下のカスタマイズを施しています：

### 1. Kong API Gatewayへの置き換え ✨

**変更内容:**
- Spring Cloud Gatewayを**Kong API Gateway**に置き換え
- Kubernetesネイティブなイングレスコントローラーとして実装
- 高度なAPI管理機能を追加

**メリット:**
- エンタープライズグレードのAPI管理
- プラグインエコシステム（レート制限、認証、ロギングなど）
- Prometheusメトリクス統合
- より優れたパフォーマンスとスケーラビリティ

### 2. Python版GenAI Serviceの追加 🐍

**新規追加:**
- FastAPI + LangChainベースのPython実装
- Java版と同等の機能を提供
- ポート8085で並行稼働可能

**特徴:**
- LangChain Agentによる会話型AI
- Chromaベクターストアを使用したRAG
- OpenAI / Azure OpenAI対応
- 詳細は[genai-python/README.md](genai-python/README.md)を参照

**比較:**

| 項目 | Java版 | Python版 |
|-----|--------|---------|
| フレームワーク | Spring Boot | FastAPI |
| AI統合 | Spring AI | LangChain |
| ベクターストア | SimpleVectorStore | Chroma |
| ポート | 8084 | 8085 |
| Kong パス | `/api/genai` | `/api/genai-python` |

### 3. Zipkin トレーシングの無効化 🔧

**変更内容:**
- GenAI Service（Java版）のZipkin依存を削除
- CrashLoopBackOffの問題を解決

**理由:**
- Zipkinサーバーが未デプロイの環境でのエラー回避
- シンプルなデプロイメント構成

**実装:**
```yaml
# k8s/genai-service/deployment.yaml
env:
- name: MANAGEMENT_TRACING_ENABLED
  value: "false"
```

### 4. Kubernetes最適化

**追加機能:**
- k3s対応のデプロイメント設定
- NodePortサービスでの外部アクセス
- ヘルスチェックプローブの最適化
- リソース制限の適切な設定

---

## 🏗️ アーキテクチャ

このプロジェクトは、従来の Spring Cloud Gateway を Kong API Gateway に置き換え、レート制限、認証、高度なルーティングなどの強化された API 管理機能を提供します。

```
┌─────────────────────────────────────────────────────────────┐
│                        Kong API Gateway                      │
│         (NodePort: 30080/30443/30081 → NLB: 30080/30443/30081) │
└──────────────┬──────────────┬──────────────┬────────────────┘
               │              │              │
       ┌───────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
       │  Customers   │ │  Visits  │ │    Vets    │
       │   Service    │ │  Service │ │  Service   │
       │   (8081)     │ │  (8082)  │ │   (8083)   │
       └──────┬───────┘ └────┬─────┘ └─────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼─────────┐
                    │ Discovery Server │
                    │    (Eureka)      │
                    │     (8761)       │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Config Server   │
                    │     (8888)       │
                    └──────────────────┘
```

### コンポーネント

#### インフラストラクチャサービス
- **Config Server** (8888): 集中設定管理
- **Discovery Server** (8761): サービスディスカバリー用の Eureka サービスレジストリ
- **Admin Server** (9090): 監視用の Spring Boot Admin

#### ビジネスサービス
- **Customers Service** (8081): ペットオーナーとペットの管理
- **Visits Service** (8082): 獣医診察記録の管理
- **Vets Service** (8083): 獣医師情報の管理
- **GenAI Service** (8084): AI 機能（Java版、Spring AI使用）
- **GenAI Python Service** (8085): AI 機能（Python版、FastAPI + LangChain使用）✨ **NEW**

#### API Gateway
- **Kong Gateway**: Spring Cloud Gateway を置き換える API ゲートウェイ
  - トラフィックルーティングとロードバランシング
  - レート制限とスロットリング
  - CORS 処理
  - リクエスト/レスポンス変換
  - メトリクス収集（Prometheus）

## 🔧 前提条件

### 必要なツール
- **Kubernetes**: k3s、k8s、または任意の Kubernetes クラスター (v1.24+)
- **kubectl**: Kubernetes CLI ツール
- **Helm**: Kubernetes 用パッケージマネージャー (v3.0+)
- **Git**: バージョン管理
- **Docker**: Python版GenAI Serviceのビルドに必要

### Docker権限の設定（重要）

Python版GenAI Serviceをビルドする場合、一般ユーザーがdockerコマンドを実行できる必要があります。

```bash
# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# 設定を反映（以下のいずれか）
# 方法1: セッション再ログイン（推奨）
exit
# SSH/ターミナルに再接続

# 方法2: 新しいグループセッションを開始
newgrp docker

# 確認: dockerコマンドがsudoなしで実行できることを確認
docker ps
docker images
```

**注意**: dockerグループへの追加は、rootユーザーと同等の権限を付与することになります。セキュリティ上のリスクを理解した上で実施してください。

### システム要件
- **メモリ**: 最低 4GB RAM (8GB 推奨)
- **CPU**: 2+ コア
- **ディスク**: 10GB 以上の空き容量

### 前提条件の確認

```bash
# Kubernetes の確認
kubectl version --client

# Helm の確認
helm version

# クラスター接続の確認
kubectl cluster-info
```

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/knakagami/o11y-kong-petclinic.git
cd o11y-kong-petclinic
```

### 2. マイクロサービスのデプロイ

```bash
# スクリプトに実行権限を付与
chmod +x scripts/*.sh

# すべての Spring PetClinic サービスをデプロイ
./scripts/deploy-services.sh
```

このスクリプトは以下を実行します：
1. `petclinic` namespace の作成
2. Config Server のデプロイと起動待機
3. Discovery Server (Eureka) のデプロイ
4. すべてのビジネスサービスを並行デプロイ
5. Admin Server のデプロイ

### 3. Kong API Gateway のデプロイ

```bash
# Ingress Controller 付き Kong Gateway をデプロイ
./scripts/deploy-kong.sh
```

このスクリプトは以下を実行します：
1. Kong Helm リポジトリの追加
2. カスタム値を使用した Helm による Kong のインストール
3. ルーティング用 Kong Ingress リソースの適用
4. プラグイン（CORS、レート制限、Prometheus）の設定

### 4. デプロイの確認

```bash
# すべての Pod が実行中であることを確認
kubectl get pods -n petclinic

# サービスの確認
kubectl get services -n petclinic

# Kong Pod の確認
kubectl get pods -n kong

# Ingress リソースの確認
kubectl get ingress -n petclinic
```

## 🌐 API エンドポイント

### Kong Gateway 経由（NodePort + AWS NLB）

すべての API は Kong Gateway 経由でアクセス可能です：
- **AWS NLB経由**: `http://<NLB-DNS>:30080` (NLB → k3s NodePort 30080)
- **ローカル（k3sノード上）**: `http://localhost:30080` または `http://<k3s-node-ip>:30080`

> **注意:** Kong Gatewayは`NodePort`サービスとして動作し、AWS NLBが外部からのリクエストを受け付けます。
> - 外部アクセス: NLBのポート30080/30443/30081を使用
> - 内部アクセス: k3sノードのNodePort 30080/30443/30081を使用（同じポート番号）

#### Customers Service

```bash
# すべての顧客を一覧表示
GET http://localhost:30080/api/customer/owners

# ID で顧客を取得
GET http://localhost:30080/api/customer/owners/{ownerId}

# 新しい顧客を作成
POST http://localhost:30080/api/customer/owners
Content-Type: application/json
{
  "firstName": "太郎",
  "lastName": "山田",
  "address": "東京都渋谷区1-2-3",
  "city": "東京",
  "telephone": "0312345678"
}

# 姓で顧客を検索
GET http://localhost:30080/api/customer/owners/*/lastname/{lastName}

# ペットタイプを取得
GET http://localhost:30080/api/customer/petTypes
```

#### Visits Service

```bash
# ペットの診察記録を取得
GET http://localhost:30080/api/visit/owners/*/pets/{petId}/visits

# 新しい診察記録を作成
POST http://localhost:30080/api/visit/owners/*/pets/{petId}/visits
Content-Type: application/json
{
  "date": "2024-01-15",
  "description": "定期健診"
}
```

#### Vets Service

```bash
# すべての獣医師を一覧表示
GET http://localhost:30080/api/vet/vets
```

#### GenAI Service（Java版）

```bash
# チャットボットAPI
POST http://localhost:30080/api/genai/chatclient
Content-Type: text/plain

飼い主を全員教えてください
```

#### GenAI Python Service ✨

```bash
# チャットボットAPI（Python版）
POST http://localhost:30080/api/genai-python/chatclient
Content-Type: text/plain

獣医師を全員教えてください

# サービス情報
GET http://localhost:30080/api/genai-python/info

# ヘルスチェック
GET http://localhost:30080/api/genai-python/health
```

#### Admin Server

```bash
# Spring Boot Admin UI にアクセス
GET http://localhost:30080/admin
```

### curl コマンド例

```bash
# すべての獣医師を取得
curl http://localhost:30080/api/vet/vets

# すべてのペットタイプを取得
curl http://localhost:30080/api/customer/petTypes

# すべてのオーナーを取得
curl http://localhost:30080/api/customer/owners

# 新しいオーナーを作成
curl -X POST http://localhost:30080/api/customer/owners \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "花子",
    "lastName": "佐藤",
    "address": "大阪府大阪市北区4-5-6",
    "city": "大阪",
    "telephone": "0667890123"
  }'
```

## 🐍 GenAI Python Service

このプロジェクトには、FastAPIとLangChainを使用したPython実装のGenAI Serviceが含まれています。

### 主な機能

- **会話型AIチャットボット**: OpenAI / Azure OpenAI GPTモデル使用
- **Function Calling**: 飼い主/ペット管理、獣医師検索
- **RAG機能**: Chromaベクターストアによる獣医師データの意味検索
- **会話履歴**: 10メッセージまでのコンテキスト保持

### ローカルビルドとデプロイ

#### 1. Dockerイメージのビルド

```bash
cd genai-python
chmod +x build-docker.sh
./build-docker.sh
```

#### 2. k3sへのイメージインポート

```bash
# イメージをk3sにインポート
docker save genai-python:latest | sudo k3s ctr images import -
```

#### 3. OpenAI APIキーの設定

```bash
# Kubernetes Secretとして設定
kubectl create secret generic genai-secrets \
  --from-literal=openai-api-key="sk-your-api-key-here" \
  -n petclinic

# または、deploymentの環境変数を直接編集
kubectl edit deployment genai-python -n petclinic
```

#### 4. デプロイ

```bash
# GenAI Python Serviceのみデプロイ
kubectl apply -f k8s/genai-python/

# または、全サービス一括デプロイ（スクリプト使用）
./scripts/deploy-services.sh
```

#### 5. 動作確認

```bash
# Pod状態確認
kubectl get pods -n petclinic -l app=genai-python

# ログ確認
kubectl logs -f deployment/genai-python -n petclinic

# Kong経由でテスト
curl -X POST http://localhost:30080/api/genai-python/chatclient \
  -H "Content-Type: text/plain" \
  -d "飼い主を全員教えてください"
```

### Java版との違い

| 項目 | Java版 | Python版 |
|-----|--------|---------|
| フレームワーク | Spring Boot + Spring AI | FastAPI + LangChain |
| ベクターストア | SimpleVectorStore | Chroma |
| デプロイ | 公式イメージ使用 | ローカルビルド必須 |
| ポート（K8s） | 8084 | 8085 |
| Kong パス | `/api/genai` | `/api/genai-python` |
| 起動時間 | 約120秒 | 約30秒 |

### トラブルシューティング

詳細なトラブルシューティング情報は [genai-python/README.md](genai-python/README.md) を参照してください。

---

## 📦 デプロイの詳細

### Namespace

すべての PetClinic リソースは `petclinic` namespace にデプロイされ、Kong は `kong` namespace にデプロイされます。

### リソース制限

各サービスには以下のデフォルトリソース設定があります：

```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
```

### ヘルスチェック

すべてのサービスには以下が含まれます：
- **Liveness Probe**: Pod が生きていることを確認
- **Readiness Probe**: Pod がトラフィックを受け入れる準備ができていることを確認

プローブは Spring Boot Actuator の `/actuator/health` エンドポイントを使用します。

### サービスの依存関係

デプロイは依存関係を尊重して以下の順序で行われます：
1. Config Server（依存関係なし）
2. Discovery Server（Config Server に依存）
3. ビジネスサービス（Config Server + Discovery Server に依存）
4. Admin Server（Config Server + Discovery Server に依存）

## 🔐 Kong Gateway 設定

### NodePort + NLB構成

Kong Gateway は Kubernetes NodePort を使用し、AWS NLB 経由で公開されています：

| 層 | HTTP | HTTPS | Admin |
|----|------|-------|-------|
| **外部アクセス（NLB）** | 30080 | 30443 | 30081 |
| **NodePort（k3s）** | 30080 | 30443 | 30081 |
| **Kong内部** | 8000 | 8443 | 8001 |

**アクセス方法:**
```bash
# NLB経由（外部から）- 推奨
curl http://<NLB-DNS>:30080/api/vet/vets

# NodePort経由（k3sノード上から）
curl http://localhost:30080/api/vet/vets

# Admin API（NLB経由）
curl http://<NLB-DNS>:30081/status

# Admin API（NodePort経由）
curl http://localhost:30081/status
```

### AWS NLB設定ガイド

#### 必要なNLBリスナーとターゲットグループ設定

**注意**: この設定では、NLBのリスナーポートとターゲットグループのポートが同じです。

| リスナー（外部） | ターゲットグループ（EC2） | 説明 |
|----------------|------------------------|------|
| TCP 30080 | 30080 | HTTPプロキシ |
| TCP 30443 | 30443 | HTTPSプロキシ（オプション） |
| TCP 30081 | 30081 | Admin API |

#### 設定手順

1. **ターゲットグループを作成（3つ）**

   **HTTPプロキシ用:**
   - プロトコル: TCP
   - ポート: **30080** ← NodePort
   - ターゲット: EC2インスタンス（k3sノード）
   - ヘルスチェック: TCP 30080

   **HTTPSプロキシ用（オプション）:**
   - プロトコル: TCP
   - ポート: **30443** ← NodePort
   - ターゲット: EC2インスタンス（k3sノード）
   - ヘルスチェック: TCP 30443

   **Admin API用:**
   - プロトコル: TCP
   - ポート: **30081** ← NodePort
   - ターゲット: EC2インスタンス（k3sノード）
   - ヘルスチェック: TCP 30081

2. **NLBリスナーを作成**
   - リスナー1: ポート 30080 → HTTPプロキシ用ターゲットグループ
   - リスナー2: ポート 30443 → HTTPSプロキシ用ターゲットグループ
   - リスナー3: ポート 30081 → Admin API用ターゲットグループ

#### セキュリティグループ設定

EC2インスタンスのセキュリティグループで以下のポートを開放：
```
インバウンドルール:
- TCP 30080 (NLBから) - HTTP Proxy
- TCP 30443 (NLBから) - HTTPS Proxy (オプション)
- TCP 30081 (NLBから) - Admin API
```

#### 確認手順

```bash
# Kong ServiceがNodePortで動作しているか確認
kubectl get svc -n kong

# 期待される出力:
# NAME                  TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)
# kong-gateway-proxy    NodePort   10.x.x.x        <none>        8000:30080/TCP,8443:30443/TCP
# kong-gateway-admin    NodePort   10.x.x.x        <none>        8001:30081/TCP

# NodePort経由でローカルからアクセスできるか確認
curl http://localhost:30080
curl http://localhost:30081/status
```

### Ingress リソース

Kong ルートは Kubernetes Ingress リソースを使用して設定されます：

```yaml
/api/customer/* → customers-service:8081
/api/visit/*    → visits-service:8082
/api/vet/*      → vets-service:8083
/api/genai/*    → genai-service:8084
/admin/*        → admin-server:9090
```

### プラグイン

以下の Kong プラグインが設定されています：

#### レート制限
- 制限: クライアントあたり毎分 100 リクエスト
- ポリシー: ローカル（インメモリ）

#### CORS
- オリジン: `*`（すべてのオリジンを許可）
- メソッド: GET、POST、PUT、DELETE、PATCH、OPTIONS
- 資格情報: 有効

#### Prometheus
- Kong のメトリクスエンドポイントでメトリクスを公開
- すべてのサービスのリクエスト/レスポンスメトリクスを収集

### Kong Admin API

`http://localhost:30081` で Kong Admin API にアクセス：

```bash
# Kong ステータスを確認
curl http://localhost:30081/status

# すべてのサービスを一覧表示
curl http://localhost:30081/services

# すべてのルートを一覧表示
curl http://localhost:30081/routes

# メトリクスを表示
curl http://localhost:30081/metrics
```

## 📊 監視と可観測性

### Spring Boot Admin

Spring Boot Admin ダッシュボードにアクセス：

```bash
# Kong Gateway 経由
http://localhost:30080/admin

# 直接アクセス（クラスター内）
http://admin-server.petclinic.svc.cluster.local:9090
```

### Eureka ダッシュボード

Eureka で登録されたサービスを表示：

```bash
# Eureka UI にアクセスするためのポートフォワード
kubectl port-forward -n petclinic svc/discovery-server 8761:8761

# ブラウザで開く
http://localhost:8761
```

### Kong メトリクス

Kong は Prometheus メトリクスを公開します：

```bash
# メトリクスエンドポイントにアクセス
curl http://localhost:30081/metrics
```

### サービスログ

```bash
# 特定のサービスのログを表示
kubectl logs -f deployment/customers-service -n petclinic

# Kong のログを表示
kubectl logs -f deployment/kong-controller -n kong

# namespace 内のすべてのログを表示
kubectl logs -f -n petclinic --all-containers=true
```

## 🔍 トラブルシューティング

### サービスが起動しない

```bash
# Pod のステータスを確認
kubectl get pods -n petclinic

# 問題のある Pod を詳しく確認
kubectl describe pod <pod-name> -n petclinic

# ログを確認
kubectl logs <pod-name> -n petclinic
```

### Config Server の問題

```bash
# Config Server のログを確認
kubectl logs deployment/config-server -n petclinic

# Config Server にアクセス可能か確認
kubectl exec -it deployment/customers-service -n petclinic -- \
  curl http://config-server:8888/actuator/health
```

### Discovery Server の問題

```bash
# Eureka のログを確認
kubectl logs deployment/discovery-server -n petclinic

# ポートフォワードして UI を確認
kubectl port-forward -n petclinic svc/discovery-server 8761:8761
# http://localhost:8761 を開く
```

### Kong Gateway の問題

```bash
# Kong Pod のステータスを確認
kubectl get pods -n kong

# Kong のログを確認
kubectl logs -f deployment/kong-controller -n kong

# Kong の設定を確認
kubectl get ingress -n petclinic
kubectl get kongplugin -n petclinic
```

### ネットワーク接続

```bash
# サービス間通信をテスト
kubectl exec -it deployment/customers-service -n petclinic -- \
  curl http://discovery-server:8761/actuator/health

# Kong からバックエンドサービスへのテスト
kubectl exec -it -n kong deployment/kong-gateway -- \
  curl http://customers-service.petclinic.svc.cluster.local:8081/actuator/health
```

### よくある問題

1. **Pod が CrashLoopBackOff 状態**
   - 依存サービス（Config/Discovery）が準備完了しているか確認
   - リソース制限を超えていないか確認
   - アプリケーションログを確認

2. **Kong から 503 Service Unavailable**
   - バックエンドサービスが実行中か確認
   - Ingress 設定を確認
   - サービスが Eureka に登録されているか確認

3. **起動が遅い**
   - サービスの完全起動には 2〜3 分かかる場合があります
   - Readiness Probe が通過するまで待機
   - リソース制約を確認

## 🧹 クリーンアップ

すべてのデプロイされたリソースを削除するには：

```bash
# クリーンアップスクリプトを実行
./scripts/cleanup.sh

# または手動で namespace を削除
kubectl delete namespace petclinic
kubectl delete namespace kong
```

## 📚 追加リソース

- [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices)
- [Kong Gateway ドキュメント](https://docs.konghq.com/)
- [Kong Ingress Controller](https://docs.konghq.com/kubernetes-ingress-controller/)
- [Spring Cloud ドキュメント](https://spring.io/projects/spring-cloud)

## 🤝 コントリビューション

コントリビューションを歓迎します！遠慮なく Pull Request を提出してください。

## 📄 ライセンス

このプロジェクトは Apache License 2.0 でライセンスされている Spring PetClinic をベースにしています。

## 👥 作者

- [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices) をベースにしています
- Kong 統合と Kubernetes デプロイ設定は **Cursor AI** によって生成されました

## 🤖 AI 生成コードについて

このプロジェクトのすべてのコード、設定ファイル、デプロイメントスクリプトは **Cursor AI** によって自動生成されています。

### 含まれるもの
- Kubernetes マニフェスト（すべてのサービス）
- Kong Gateway Helm 設定
- デプロイメント自動化スクリプト
- ドキュメント

### 注意事項
- ⚠️ AI 生成コードには予期しないバグや設定ミスが含まれる可能性があります
- ⚠️ 本番環境で使用する前に、すべての設定を慎重に検証してください
- ⚠️ セキュリティ設定、リソース制限、ネットワークポリシーを本番環境に合わせて調整してください
- ⚠️ このプロジェクトはデモンストレーションと学習目的で提供されています

---

**注意**: これはデモンストレーションプロジェクトです。本番環境で使用する場合は、以下を検討してください：
- 認証と認可の追加
- 適切なシークレット管理の実装
- TLS/SSL 証明書の設定
- 自動バックアップの設定
- 適切な監視とアラートの実装
- ステートフルサービス用の永続ストレージの使用
- セキュリティスキャンとコンプライアンスチェック
- リソース制限の調整とパフォーマンステスト
