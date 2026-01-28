# Spring PetClinic Microservices with Kong API Gateway & Splunk Observability

Spring PetClinicをマイクロサービスとして実装し、Kong API Gateway、OpenTelemetry、Splunk Observability Cloudを統合してKubernetes (k3s) 上にデプロイします。

> **⚠️ 重要な注意事項**
> 
> このプロジェクトのコードは **Cursor AI** によって生成されました。
> - すべてのKubernetesマニフェスト、デプロイメントスクリプト、設定ファイルはAIによって自動生成されています
> - 予期しない動作や設定ミスが含まれる可能性があります
> - **このプロジェクトはデモンストレーション・学習目的であり、商用利用は想定していません**
> - 本番環境での使用は推奨されません

## 📋 目次

- [プロジェクト概要](#プロジェクト概要)
- [アーキテクチャ](#アーキテクチャ)
- [主要コンポーネント](#主要コンポーネント)
- [前提条件](#前提条件)
- [セットアップ手順](#セットアップ手順)
- [デプロイ手順](#デプロイ手順)
- [アクセス方法](#アクセス方法)
- [オブザーバビリティ](#オブザーバビリティ)
- [クリーンアップ](#クリーンアップ)

---

## 🎯 プロジェクト概要

このプロジェクトは、[Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices)をベースに、エンタープライズグレードのAPI管理とオブザーバビリティを追加した実装です。

### 主な特徴

1. **Kong API Gateway** - Spring Cloud Gatewayの代わりにKongを使用
   - Kubernetes Ingress Controller
   - Lua Pre-functionによる高度なパス書き換え
   - OpenTelemetry統合による分散トレーシング

2. **Splunk Observability Cloud統合** - フルスタックオブザーバビリティ
   - OpenTelemetry Collectorによるメトリクス・トレース・ログ収集
   - OpenTelemetry Operatorによる自動計装（Java）、ビルトイン計装（Python）
   - APM、Infrastructure Monitoring、Log Observer

3. **Angular SPA Web UI** - ブラウザからアクセス可能なフロントエンド
   - ペットオーナー、ペット、獣医師の管理
   - AI チャット機能（GenAI Service）

4. **Python版GenAI Service** - FastAPI + LangChain 1.x実装
   - OpenAI API統合
   - RAG（Retrieval-Augmented Generation）
   - 会話型AIエージェント

---

## 🏗️ アーキテクチャ

### システム全体図

```
┌──────────────────────────────────────────────────────────────────┐
│                       External Access                            │
│                                                                  │
│  Browser / API Client  →  k3s NodePort (30080)                  │
└──────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────┐
│                      Kong API Gateway                            │
│                     (Ingress Controller)                         │
│                                                                  │
│  • Lua Pre-function: /api/gateway/** → /owners/**               │
│  • OpenTelemetry Plugin: Trace Context Propagation              │
│  • CORS Plugin: Cross-Origin Support                            │
└──────────────────────────────────────────────────────────────────┘
                      ↓               ↓               ↓
┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Frontend    │  │   Customers   │  │    Visits     │  │     Vets      │
│   (Angular)   │  │    Service    │  │    Service    │  │    Service    │
│               │  │               │  │               │  │               │
│   Port 8080   │  │   Port 8081   │  │   Port 8082   │  │   Port 8083   │
└───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘
                                          ↓
                   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
                   │     GenAI     │  │ GenAI-Python  │  │     Admin     │
                   │    Service    │  │   (FastAPI)   │  │    Server     │
                   │               │  │               │  │               │
                   │   Port 8084   │  │   Port 8085   │  │   Port 9090   │
                   └───────────────┘  └───────────────┘  └───────────────┘
                            ↓                 ↓
┌──────────────────────────────────────────────────────────────────┐
│               Infrastructure Services                            │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐                          │
│  │    Config     │  │   Discovery   │                          │
│  │    Server     │  │    Server     │                          │
│  │               │  │   (Eureka)    │                          │
│  │   Port 8888   │  │   Port 8761   │                          │
│  └───────────────┘  └───────────────┘                          │
└──────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────┐
│               Observability Stack                                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │      Splunk OpenTelemetry Collector (DaemonSet)            │ │
│  │                                                            │ │
│  │  • Auto-instrumentation (Java/Python)                     │ │
│  │  • Metrics, Traces, Logs collection                       │ │
│  │  • Export to Splunk Observability Cloud                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                  ↓
                     ┌─────────────────────────┐
                     │  Splunk Observability   │
                     │         Cloud           │
                     │                         │
                     │  • APM                  │
                     │  • Infrastructure       │
                     │  • Log Observer         │
                     └─────────────────────────┘
```

### リクエストフロー

#### 1. Web UIへのアクセス

```
Browser Request: GET http://localhost:30080/
                                ↓
                        Kong API Gateway
                    (Ingress Match: /)
                                ↓
                        Frontend Service
                         (Port 8080)
                                ↓
        Angular SPA (index.html, JS, CSS) を返却
                                ↓
                    Browser でレンダリング
```

#### 2. Angular SPA から Backend API へのリクエスト

```
Browser (Angular SPA) 内の JavaScript が実行:
  → fetch('/api/gateway/owners/3')
                ↓
        Kong API Gateway
    (Ingress Match: /api/gateway/owners/**)
                ↓
        Lua Pre-function Plugin:
          path:gsub("^/api/gateway/owners", "/owners")
          → /api/gateway/owners/3 を /owners/3 に書き換え
                ↓
        OpenTelemetry Plugin:
          - W3C Trace Context を注入 (Traceparent header)
          - Kong span を OTel Collector へエクスポート
                ↓
        Customers Service (Port 8081)
          Receives: GET /owners/3
                ↓
        OTel Java Agent (Auto-instrumentation):
          - Trace Context を抽出
          - Service span を作成
          - OTel Collector へエクスポート
                ↓
        Owner データ (JSON) を返却
                ↓
        Kong API Gateway
          → Browser (Angular SPA) へレスポンス
                ↓
    Browser で Owner 情報を表示
```

#### 3. Splunk Observability Cloud での可視化

```
OTel Collector が受信したトレース:
  Kong span + Customers Service span
                ↓
  Splunk Observability Cloud へエクスポート
                ↓
    APM: 完全なトレース可視化 (Kong → Customers)
    Service Map: サービス間依存関係の可視化
    Metrics: レイテンシ、エラー率などのパフォーマンス指標
```

---

## 🧩 主要コンポーネント

### Kong API Gateway

**役割**: API管理とルーティング

**バージョン**:
- Kong Gateway: 3.8
- Kong Ingress Controller: 3.3

**主要機能**:
- **Kubernetes Ingress Controller**: Kubernetesネイティブな設定管理
- **Lua Pre-function Plugin**: 高度なパス書き換え
  - `/api/gateway/owners/**` → `/owners/**`
  - `/api/gateway/pets/**` → `/pets/**`
  - `/api/gateway/visits/**` → `/visits/**`
- **OpenTelemetry Plugin**: 分散トレーシング
  - W3C Trace Context propagation
  - Baggage propagation
  - OTLP export to Splunk OTel Collector
- **CORS Plugin**: クロスオリジンリクエストサポート

**デプロイ方式**: Helm Chart (NodePort service)

### Splunk OpenTelemetry Collector

**役割**: テレメトリーデータの収集と転送

**デプロイ形態**:
- **DaemonSet**: 各ノードで実行
- **Operator**: 自動計装の管理

**自動計装**:
- **Java services**: OpenTelemetry Java Agent
  - OpenTelemetry Operatorによる自動インジェクション
  - Annotation: `instrumentation.opentelemetry.io/inject-java: "default/splunk-otel-collector"`
- **Python services (GenAI Python)**: OpenTelemetry Python Agent
  - Dockerイメージにビルトインされたゼロコード計装（`opentelemetry-instrument`コマンド使用）
  - Operatorアノテーションは使用せず、すべての設定を環境変数で管理

**データフロー**:
```
Application → OTel Agent (Init Container) → OTel Collector (Agent) → Splunk Observability Cloud
```

### Frontend Service (Angular SPA)

**役割**: Web UIの提供

**機能**:
- 静的ファイル配信（HTML/JS/CSS）
- Angular SPAからのAPIリクエストはKong経由でバックエンドへ
- Spring Cloud Gatewayは `/api/gateway/**` のルーティングを行わない（Kongが直接処理）

**アクセスパス**:
- Web UI: `http://<NLB>:30080/`
- Angular SPAが使用するAPI: `/api/gateway/**`

### Business Services

#### Customers Service (Port 8081)
- ペットオーナーとペット情報の管理
- Endpoints: `/owners`, `/petTypes`, `/pets`

#### Visits Service (Port 8082)
- 獣医診察記録の管理
- Endpoints: `/visits`

#### Vets Service (Port 8083)
- 獣医師情報の管理
- Endpoints: `/vets`

#### GenAI Python Service (Kubernetesサービスポート: 8085、コンテナ内部ポート: 8084)
- AI チャット機能（FastAPI + LangChain 1.x）
- OpenAI API統合
- Endpoints: `/chatclient`, `/health`, `/info`
- 注意: コンテナ内部では8084ポートで動作し、Kubernetesサービスが8085にマッピング

#### Admin Server (Port 9090)
- Spring Boot Admin による監視
- Endpoint: `/admin`

### Infrastructure Services

#### Config Server (Port 8888)
- Spring Cloud Config による設定管理

#### Discovery Server (Port 8761)
- Eureka サービスレジストリ

---

## 🔧 前提条件

### 必要なツール

- **Kubernetes**: k3s、k8s、または任意のKubernetesクラスター (v1.24+)
- **kubectl**: Kubernetes CLI ツール
- **Helm**: Kubernetes パッケージマネージャー (v3.0+)
- **Git**: バージョン管理
- **Docker**: Python版GenAI Serviceのビルドに必要（オプション）

### システム要件

推奨スペック（OpenTelemetry Agent含む）:
- **メモリ**: 16GB 以上
- **CPU**: 4コア 以上
- **ディスク**: 20GB 以上

> **注意**: OpenTelemetry Java/Python Agentは追加のメモリ・CPUリソースを消費します。
> 各アプリケーションPodのメモリ制限は1.5GB、リクエストは1GBに設定されています。

### Docker権限の設定（Python GenAI Serviceをビルドする場合）

```bash
# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# セッション再ログイン（推奨）
exit
# SSH/ターミナルに再接続

# または新しいグループセッションを開始
newgrp docker

# 確認
docker ps
docker images
```

**注意**: dockerグループへの追加は、rootユーザーと同等の権限を付与します。セキュリティリスクを理解した上で実施してください。

### Helm設定

k3sを使用している場合、Helmが正しくKubernetesクラスターにアクセスできるよう設定します：

```bash
# KUBECONFIG環境変数を設定
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# .bashrcに追加（永続化）
echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
source ~/.bashrc

# 確認
helm version
kubectl get nodes
```

### 外部サービスの準備

#### 1. Splunk Observability Cloud

**必須**: メトリクス・トレース・ログを収集するため

1. Splunk Observability Cloudアカウントを作成: https://www.splunk.com/en_us/download/o11y-cloud-free-trial.html
2. 以下の情報を取得:
   - **Access Token**: Settings → Access Tokens → Create New Token
   - **Realm**: Profile → Organization Settings → Realm (例: `us1`, `us2`, `eu0`, `jp0`)

#### 2. OpenAI API Key（AI チャット機能を使用する場合）

1. OpenAIアカウントを作成: https://platform.openai.com/
2. API Keyを作成: API Keys → Create new secret key
3. APIキーをコピー（形式: `sk-...`）

---

## 🚀 セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/knakagami/o11y-kong-petclinic.git
cd o11y-kong-petclinic
```

### 2. Kubernetes Secretsの作成

#### 2.1 Splunk Observability Cloud用Secret

OpenTelemetry Collectorの設定ファイルをコピーして編集:

```bash
# user-values.yamlのテンプレートをコピー
cd otel
cp user-values-template.yaml user-values.yaml

# 編集: Access TokenとRealmを設定
nano user-values.yaml  # または vi, vim, code など
```

`user-values.yaml` の内容:

```yaml
# Splunk Observability Cloud connection settings
splunkObservability:
  accessToken: "YOUR_SPLUNK_ACCESS_TOKEN_HERE"  # ← ここにAccess Tokenを設定
  realm: "us1"  # ← ここにRealmを設定（例: us1, us2, eu0, jp0）
  
  # Optional: Enable additional features
  profilingEnabled: false
  secureAppEnabled: false

# Cluster identification
clusterName: "o11y-kong-petclinic-cluster"  # ← クラスター名を変更可能
environment: "production"  # ← 環境名を変更可能

# Optional: Splunk Platform (Enterprise/Cloud) integration
# Uncomment if you want to send logs to Splunk Platform
# splunkPlatform:
#   endpoint: "https://your-splunk-instance:8088/services/collector"
#   token: "YOUR_HEC_TOKEN_HERE"
#   index: "main"
#   source: "kubernetes"
#   sourcetype: "_json"
#   insecureSkipVerify: false
```

> **重要**: `user-values.yaml` は `.gitignore` に含まれており、誤ってコミットされることはありません。

#### 2.2 GenAI Service用Secret（AI チャット機能を使用する場合）

```bash
# OpenAI API Keyを含むSecretを作成
kubectl create namespace petclinic

kubectl create secret generic genai-secrets \
  --from-literal=openai-api-key=YOUR_OPENAI_API_KEY_HERE \
  -n petclinic

# 確認
kubectl get secret genai-secrets -n petclinic
kubectl describe secret genai-secrets -n petclinic
```

**代替方法（YAMLファイルから作成）**:

```bash
# secret.yaml を作成（注意: このファイルはGitにコミットしないこと）
cat << EOF > /tmp/genai-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: genai-secrets
  namespace: petclinic
type: Opaque
stringData:
  openai-api-key: "YOUR_OPENAI_API_KEY_HERE"
EOF

kubectl apply -f /tmp/genai-secrets.yaml
rm /tmp/genai-secrets.yaml  # 作成後は削除
```

### 3. Python GenAI Serviceのビルド（オプション）

Python版GenAI Serviceを使用する場合、Dockerイメージをビルドします：

```bash
cd genai-python

# Dockerイメージをビルド
docker build -t genai-python:latest .

# k3sにイメージをインポート（k3s使用時）
docker save genai-python:latest | sudo k3s ctr images import -

# 確認
sudo k3s ctr images ls | grep genai-python

cd ..
```

詳細は [genai-python/README.md](genai-python/README.md) を参照してください。

---

## 📦 デプロイ手順

### ステップ1: マイクロサービスのデプロイ

すべてのSpring Bootマイクロサービスとフロントエンドをデプロイします：

```bash
./scripts/deploy-services.sh
```

このスクリプトは以下を実行します：
1. `petclinic` namespaceの作成
2. Config Serverのデプロイ（設定管理）
3. Discovery Serverのデプロイ（Eureka）
4. ビジネスサービスのデプロイ（customers, visits, vets, genai, genai-python）
5. Admin Serverのデプロイ（監視）
6. Frontend（Angular SPA）のデプロイ

**デプロイ時間**: 約5-10分（イメージのダウンロードと起動を含む）

### ステップ2: Kong API Gatewayのデプロイ

Kong Gatewayとルーティングルールをデプロイします：

```bash
./scripts/deploy-kong.sh
```

このスクリプトは以下を実行します：
1. Kong Helmリポジトリの追加
2. `kong` namespaceの作成
3. Kong Gateway + Ingress ControllerのHelmインストール
4. Ingress資源とプラグイン設定の適用
   - Lua Pre-functionプラグイン（パス書き換え）
   - OpenTelemetryプラグイン（トレース伝搬）
   - CORSプラグイン

**デプロイ時間**: 約2-3分

### ステップ3: OpenTelemetry Collectorのデプロイ

Splunk OpenTelemetry CollectorとOperatorをデプロイします：

```bash
cd otel
./deploy-otel.sh
```

このスクリプトは以下を実行します：
1. Splunk OTel Collector Helmリポジトリの追加
2. `values.yaml` と `user-values.yaml` をマージしてインストール
3. Collector Agentの起動（DaemonSet）
4. Operatorの起動（自動計装管理）
5. 必要な依存関係（cert-managerなど）はHelmチャートが自動的にインストール

**デプロイ時間**: 約3-5分

詳細は [otel/README.md](otel/README.md) を参照してください。

### ステップ4: デプロイの確認

すべてのPodが`Running`状態になるまで待ちます：

```bash
# Petclinic サービスの確認
kubectl get pods -n petclinic

# Kong Gatewayの確認
kubectl get pods -n kong

# OpenTelemetry Collectorの確認（defaultネームスペースにデプロイ）
kubectl get pods -n default -l app=splunk-otel-collector

# すべてのIngressの確認
kubectl get ingress -n petclinic

# すべてのサービスの確認
kubectl get svc -A
```

**期待される出力（petclinic namespace）**:
```
NAME                             READY   STATUS    RESTARTS   AGE
admin-server-xxxxxxxxxx-xxxxx    1/1     Running   0          5m
config-server-xxxxxxxxxx-xxxxx   1/1     Running   0          6m
customers-service-xxx-xxxxx      1/1     Running   0          4m
discovery-server-xxx-xxxxx       1/1     Running   0          5m
frontend-xxxxxxxxxx-xxxxx        1/1     Running   0          3m
genai-python-xxxxxxxxxx-xxxxx    1/1     Running   0          3m
genai-service-xxxxxxxxxx-xxxxx   1/1     Running   0          3m
vets-service-xxxxxxxxxx-xxxxx    1/1     Running   0          4m
visits-service-xxxxxxxxxx-xxxxx  1/1     Running   0          4m
```

---

## 🌐 アクセス方法

### Web UI（ブラウザから）

Spring PetClinicのAngular製Web UIにアクセス：

```
http://<k3s-node-ip>:30080/
または
http://<NLB-DNS>:30080/  （AWS NLB使用時）
```

**Web UIの機能**:
- 🔍 **FIND OWNERS**: ペットオーナーの検索・一覧
- ✏️ **Owner Details**: オーナー情報の表示・編集
- 🐾 **Add New Pet**: ペットの追加
- 👨‍⚕️ **VETERINARIANS**: 獣医師の一覧
- 💬 **AI Chat**: AIチャットボット（画面右下のアイコン）

### API エンドポイント（curl / Postmanから）

Kong Gateway経由でAPIにアクセス：

**ベースURL**:
```
http://localhost:30080  （k3sノード上から）
http://<NLB-DNS>:30080  （AWS NLB経由）
```

#### Customers Service

```bash
# すべてのオーナーを一覧表示
curl http://localhost:30080/api/customer/owners

# ID でオーナーを取得
curl http://localhost:30080/api/customer/owners/3

# 新しいオーナーを作成
curl -X POST http://localhost:30080/api/customer/owners \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "太郎",
    "lastName": "山田",
    "address": "東京都渋谷区1-2-3",
    "city": "東京",
    "telephone": "0312345678"
  }'

# ペットタイプを取得
curl http://localhost:30080/api/customer/petTypes
```

#### Visits Service

```bash
# ペットの診察記録を取得
curl http://localhost:30080/api/visit/owners/3/pets/4/visits

# 新しい診察記録を作成
curl -X POST http://localhost:30080/api/visit/owners/3/pets/4/visits \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "description": "定期健診"
  }'
```

#### Vets Service

```bash
# すべての獣医師を一覧表示
curl http://localhost:30080/api/vet/vets
```

#### GenAI Python Service

```bash
# AIチャットボット
curl -X POST http://localhost:30080/api/genai/chatclient \
  -H "Content-Type: text/plain" \
  -d "飼い主を全員教えてください"

# サービス情報
curl http://localhost:30080/api/genai-python/info

# ヘルスチェック
curl http://localhost:30080/api/genai-python/health
```

#### Admin Server

```bash
# Spring Boot Admin UI にアクセス
curl http://localhost:30080/admin

# または ブラウザで開く
open http://localhost:30080/admin
```

### Kong Admin API

Kong Gatewayの設定を確認：

```bash
# Port-forward でKong Admin APIにアクセス
kubectl port-forward -n kong service/kong-gateway-admin 8001:8001

# ルート一覧を確認
curl http://localhost:8001/routes | jq '.data[] | {name, paths}'

# サービス一覧を確認
curl http://localhost:8001/services | jq '.data[] | {name, host, port}'

# プラグイン一覧を確認
curl http://localhost:8001/plugins | jq '.data[] | {name, enabled}'
```

---

## 📊 オブザーバビリティ

### OpenTelemetry 自動計装

#### Java Services

すべてのSpring Bootサービスは、OpenTelemetry Java Agentで自動計装されています。

**設定方法**:
```yaml
# k8s/*/deployment.yaml (Java Services)
metadata:
  annotations:
    # OpenTelemetry Operatorによる自動計装
    instrumentation.opentelemetry.io/inject-java: "default/splunk-otel-collector"
spec:
  containers:
  - env:
    # リソース属性の設定
    - name: OTEL_RESOURCE_ATTRIBUTES
      value: "service.namespace=petclinic,deployment.environment=o11y-custom-petclinic"
```

**効果**:
- HTTP リクエスト/レスポンスの自動トレース
- データベースクエリの自動トレース
- JVM メトリクスの自動収集
- トレースコンテキストの自動伝搬
- リソース属性の自動付与（`service.namespace=petclinic`, `deployment.environment=o11y-custom-petclinic`）

#### Python Services

GenAI Python ServiceはDockerイメージにビルトインされたOpenTelemetry Python Agentで計装されています。

**計装方式**:
- Dockerイメージのビルド時に `opentelemetry-distro` と計装ライブラリをインストール
- コンテナ起動時に `opentelemetry-instrument` コマンドでアプリケーションをラップ
- OpenTelemetry Operatorのアノテーションは**使用しない**（二重計装を回避）

**設定方法**:
```yaml
# k8s/genai-python/deployment.yaml
metadata:
  annotations:
    # Operatorアノテーションはコメントアウト（ビルトイン計装を使用）
    # instrumentation.opentelemetry.io/inject-python: "default/splunk-otel-collector"
spec:
  containers:
  - env:
    # OpenTelemetry設定（環境変数で完全制御）
    - name: OTEL_SERVICE_NAME
      value: "genai-python"
    - name: OTEL_EXPORTER_OTLP_ENDPOINT
      value: "http://splunk-otel-collector-agent.default.svc.cluster.local:4318"
    - name: OTEL_RESOURCE_ATTRIBUTES
      value: "service.namespace=petclinic,deployment.environment=o11y-custom-petclinic,..."
```

詳細は [`genai-python/Dockerfile`](genai-python/Dockerfile) と [`k8s/genai-python/deployment.yaml`](k8s/genai-python/deployment.yaml) を参照してください。

#### Spring Boot Zipkinの無効化

OpenTelemetryに一本化するため、すべてのサービスでSpring Boot Zipkinを無効化しています：

```yaml
# k8s/*/deployment.yaml
env:
- name: MANAGEMENT_TRACING_ENABLED
  value: "false"
- name: MANAGEMENT_ZIPKIN_TRACING_ENDPOINT
  value: ""
```

また、ConfigMapでも無効化：

```yaml
# k8s/*/configmap.yaml (例: frontend)
management:
  tracing:
    enabled: false
  zipkin:
    tracing:
      endpoint: ""

spring.zipkin.enabled: false
spring.sleuth.enabled: false
```

### Kong OpenTelemetry Plugin

Kong GatewayはOpenTelemetryプラグインでトレースコンテキストを伝搬します。

**設定**:
```yaml
# kong/kong-resources.yaml
kind: KongClusterPlugin
metadata:
  name: global-opentelemetry
  labels:
    global: "true"  # クラスタ全体に適用
config:
  endpoint: "http://splunk-otel-collector-agent.default.svc.cluster.local:4318/v1/traces"
  resource_attributes:
    service.name: "kong-gateway"
    service.namespace: "kong-gateway-services"
    deployment.environment: "production"  # ← otel/user-values.yaml の environment と一致させる
  propagation:
    default_format: "w3c"
    extract: ["w3c", "b3", "jaeger"]
    inject: ["w3c", "b3"]
  sampling_rate: 1.0
```

**機能**:
- W3C Trace Contextの抽出（リクエストから）
- W3C Trace Contextの注入（バックエンドへ）
- B3、Jaegerフォーマットのサポート
- OTLPエクスポート（Splunk OTel Collectorへ）

**重要な注意事項**:

1. **環境値の同期が必要**
   
   以下の3つのファイルで `deployment.environment` / `environment` の値を一致させてください：
   
   ```bash
   # 1. otel/user-values.yaml
   environment: "o11y-custom-petclinic"  # または任意の環境名
   
   # 2. kong/kong-resources.yaml
   resource_attributes:
     deployment.environment: "o11y-custom-petclinic"  # ← 一致させる
   
   # 3. k8s/*/deployment.yaml (全マイクロサービス)
   env:
   - name: OTEL_RESOURCE_ATTRIBUTES
     value: "service.namespace=petclinic,deployment.environment=o11y-custom-petclinic"  # ← 一致させる
   ```
   
   現在のデフォルト値は `o11y-custom-petclinic` です。環境を変更する場合は、これら3箇所を手動で更新してください。

2. **Kong 4.0 以降の変更**
   
   `header_type` パラメータは Kong 4.0 以降非推奨です。`propagation` 設定のみを使用してください。

---

## 🛠️ Kong Gateway 詳細設定

### Lua Pre-function による パス書き換え

Angular SPAからの `/api/gateway/**` リクエストは、Kong Lua Pre-functionプラグインで書き換えられます。

**理由**:
- Angular SPAは元々の Spring PetClinic の公式Dockerイメージを使用
- Angular SPAのコードは `/api/gateway/**` パスにハードコードされている
- ソースコードを修正せずに、Kongでパスを書き換える

**実装例（/api/gateway/owners/** → /owners/**）**:

```yaml
# kong/kong-resources.yaml
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: rewrite-gateway-owners
  namespace: petclinic
plugin: pre-function
config:
  access:
    - |
      local path = kong.request.get_path()
      local new_path = path:gsub("^/api/gateway/owners", "/owners")
      kong.service.request.set_path(new_path)
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gateway-owners-ingress
  namespace: petclinic
  annotations:
    konghq.com/plugins: rewrite-gateway-owners
spec:
  rules:
  - http:
      paths:
      - path: /api/gateway/owners
        pathType: Prefix
        backend:
          service:
            name: customers-service
            port:
              number: 8081
```

**フロー**:
```
1. Browser → /api/gateway/owners/3
2. Kong Ingress Match: /api/gateway/owners
3. Lua Pre-function:
   path:gsub("^/api/gateway/owners", "/owners")
   → /api/gateway/owners/3 → /owners/3
4. Backend → customers-service:8081/owners/3
```

**パス書き換えルール**:
| 元のパス (Angular SPA) | 書き換え後 (Backend) | Backend Service |
|----------------------|---------------------|-----------------|
| `/api/gateway/owners/**` | `/owners/**` | customers-service |
| `/api/gateway/petTypes` | `/petTypes` | customers-service |
| `/api/gateway/pets/**` | `/pets/**` | customers-service |
| `/api/gateway/visits/**` | `/visits/**` | visits-service |
| `/api/gateway/vets` | `/vets` | vets-service |

### Ingress リソース一覧

すべてのIngress リソース:

```yaml
# Frontend (Angular SPA)
/                   → frontend:8080

# Backend Services (Direct API)
/api/customer/*     → customers-service:8081
/api/visit/*        → visits-service:8082
/api/vet/*          → vets-service:8083
/api/genai/*        → genai-python:8085
/api/genai-python/* → genai-python:8085
/admin/*            → admin-server:9090

# Angular SPA Routes (Lua Pre-function)
/api/gateway/owners/**  → customers-service:8081 (/owners/**)
/api/gateway/petTypes   → customers-service:8081 (/petTypes)
/api/gateway/pets/**    → customers-service:8081 (/pets/**)
/api/gateway/visits/**  → visits-service:8082 (/visits/**)
/api/gateway/vets       → vets-service:8083 (/vets)
```

---

## 🧹 クリーンアップ

### 全リソースの削除

```bash
# OpenTelemetry Collectorの削除
helm uninstall splunk-otel-collector -n default
kubectl delete namespace cert-manager

# Kong Gatewayの削除
helm uninstall kong -n kong
kubectl delete namespace kong

# Petclinicサービスの削除
kubectl delete namespace petclinic

# 確認
kubectl get pods -A
```

### 個別サービスの削除

```bash
# 特定のサービスのみ削除
kubectl delete -f k8s/customers-service/
kubectl delete -f k8s/genai-python/

# または Deploymentのみ削除
kubectl delete deployment customers-service -n petclinic
```

---

## 📚 参考資料

### プロジェクトドキュメント

- [GenAI Python Service README](genai-python/README.md)
- [OpenTelemetry Collector README](otel/README.md)

### 外部リンク

- [Spring PetClinic Microservices (オリジナル)](https://github.com/spring-petclinic/spring-petclinic-microservices)
- [Kong Gateway Documentation](https://docs.konghq.com/gateway/latest/)
- [Kong Ingress Controller](https://docs.konghq.com/kubernetes-ingress-controller/latest/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Splunk Observability Cloud](https://docs.splunk.com/Observability/)
- [Splunk OpenTelemetry Collector](https://github.com/signalfx/splunk-otel-collector-chart)

---

## 📝 ライセンス

このプロジェクトは Apache License 2.0 の下でライセンスされています。

元のSpring PetClinicプロジェクトについては、[オリジナルリポジトリ](https://github.com/spring-petclinic/spring-petclinic-microservices)を参照してください。

---

## 🤝 コントリビューション

Issue、Pull Request、フィードバックを歓迎します！

---

**Author**: Generated with Cursor AI  
**Last Updated**: 2026-01-28
