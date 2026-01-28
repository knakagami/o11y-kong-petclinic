# GenAI Python Service

Python実装のSpring PetClinic GenAIサービスです。FastAPIとLangChainを使用して、Java版と同等の機能を提供します。

## 概要

このサービスは、ペットクリニック管理を支援するAIチャットボットを提供します。OpenAI GPTモデルを使用して、獣医師、飼い主、ペット、訪問記録に関する質問に答え、操作を実行できます。

## 主要機能

### 1. 会話型AIチャットボット
- OpenAI GPT-4o-miniまたはAzure OpenAI GPT-4oを使用
- 会話履歴を保持（メモリベース、リクエスト毎にクリア）
- 自然言語での質問応答

### 2. Function Calling（ツール呼び出し）
LLMが自動的に適切な関数を呼び出します：

- **`list_owners`**: 飼い主リストの取得
- **`add_owner_to_petclinic`**: 新しい飼い主の追加
- **`list_vets`**: 獣医師の検索（RAG使用）
- **`add_pet_to_owner`**: 飼い主へのペット追加

### 3. RAG (Retrieval-Augmented Generation)
- Chromaベクターストアを使用
- 獣医師データのセマンティック検索
- 起動時にvets-serviceからデータを自動ロード
- ディスク永続化によるコスト削減

### 4. 他サービスとの連携
- **customers-service**: 飼い主とペット管理
- **vets-service**: 獣医師情報
- **config-server**: 集中設定管理（オプション）
- **discovery-server**: サービス登録（オプション）

## 技術スタック

- **フレームワーク**: FastAPI 0.115.6
- **LLM統合**: LangChain 1.0.3、langchain-openai 1.1.2
- **ベクターストア**: Chroma 0.5.23
- **HTTPクライアント**: httpx 0.28.1
- **Python**: 3.11

## Spring版との機能対応

| 機能 | Spring版 | Python版 |
|-----|---------|---------|
| チャットAPI | Spring AI ChatClient | LangChain Agent (create_agent) |
| Function Calling | @Bean Functions | LangChain Tools |
| RAG | SimpleVectorStore | Chroma |
| メモリ | MessageChatMemoryAdvisor | ConversationBufferMemory（リクエスト毎にクリア） |
| OpenAI | spring-ai-openai | langchain-openai |
| ヘルスチェック | Spring Actuator | FastAPI endpoint |
| コンテナ内部ポート | 8084 | 8084 |
| Kubernetesサービスポート | 8084 | 8085 |

**注意**: コンテナは8084ポートでリッスンしますが、Kubernetesサービスは8085ポートにマッピングされています（[`k8s/genai-python/service.yaml`](../k8s/genai-python/service.yaml)参照）。

## セットアップ

### 前提条件

- Python 3.11以上
- Docker（コンテナビルド用）
- OpenAI APIキーまたはAzure OpenAI設定

#### Docker権限の設定

一般ユーザー（ubuntu等）でdockerコマンドを実行する場合、dockerグループへの追加が必要です：

```bash
# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# セッション再ログイン、または
newgrp docker

# 確認
docker ps
```

**注意**: dockerグループへの追加は、rootユーザーと同等の権限を付与します。

### ローカル開発環境

#### 1. 依存関係のインストール

```bash
cd genai-python
pip install -r requirements.txt
```

#### 2. 環境変数の設定

```bash
# OpenAI使用の場合
export OPENAI_API_KEY="sk-your-api-key-here"
export OPENAI_MODEL="gpt-4o-mini"  # オプション

# または Azure OpenAI使用の場合
export AZURE_OPENAI_KEY="your-azure-key"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"

# 他のサービスURL（ローカル開発用）
export CUSTOMERS_SERVICE_URL="http://localhost:8081"
export VETS_SERVICE_URL="http://localhost:8083"
```

#### 3. アプリケーションの起動

```bash
# 開発モード（自動リロード有効）
uvicorn app.main:app --reload --port 8085

# または直接実行
python -m app.main
```

#### 4. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8085/health

# チャットテスト
curl -X POST http://localhost:8085/chatclient \
  -H "Content-Type: text/plain" \
  -d "Show me all owners"
```

## Dockerビルド

### ローカルビルド

```bash
cd genai-python
./build-docker.sh
```

このスクリプトは以下を実行します:
- Dockerイメージのビルド（`genai-python:latest`）
- バージョンタグの作成（`genai-python:v1.0.0`）

または手動でビルド:

```bash
docker build -t genai-python:latest .
```

### Dockerイメージのテスト

```bash
docker run -p 8085:8084 \
  -e OPENAI_API_KEY="sk-your-key" \
  -e CUSTOMERS_SERVICE_URL="http://host.docker.internal:8081" \
  -e VETS_SERVICE_URL="http://host.docker.internal:8083" \
  genai-python:latest
```

**ポート説明**: `-p 8085:8084` はホストの8085ポートをコンテナ内部の8084ポートにマッピングします。

### k3sへのイメージインポート

```bash
# 方法1: パイプ経由
docker save genai-python:latest | sudo k3s ctr images import -

# 方法2: ファイル経由
docker save genai-python:latest -o genai-python.tar
sudo k3s ctr images import genai-python.tar
rm genai-python.tar
```

## Kubernetesデプロイ

### 前提条件

他のPetClinicサービスが既にデプロイされていること：
- config-server
- discovery-server
- customers-service
- vets-service

### OpenAI APIキーの設定

Secretを作成（オプション、環境変数でも可）：

```bash
kubectl create secret generic genai-secrets \
  --from-literal=openai-api-key="sk-your-key" \
  -n petclinic
```

デプロイメントの環境変数部分のコメントを外してSecretを参照：

```yaml
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: genai-secrets
      key: openai-api-key
```

### OpenTelemetryビルトイン計装

このサービスは**Dockerイメージにビルトインされた**OpenTelemetry計装を使用します。

#### 計装方式

OpenTelemetry Operatorのアノテーションは**使用していません**。代わりに、以下の方法で計装しています：

1. **ビルド時**: Dockerfileで計装ライブラリをインストール
   ```dockerfile
   RUN pip install --no-cache-dir -r requirements.txt
   RUN opentelemetry-bootstrap -a install
   ```

2. **起動時**: `opentelemetry-instrument` コマンドでアプリケーションをラップ
   ```dockerfile
   CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8084", "--loop", "asyncio"]
   ```

詳細は [`Dockerfile`](Dockerfile) 26-46行目を参照してください。

#### Deployment設定

[`k8s/genai-python/deployment.yaml`](../k8s/genai-python/deployment.yaml) では:

```yaml
metadata:
  annotations:
    # OpenTelemetry Operator injection is DISABLED to avoid double instrumentation
    # The application uses built-in zero-code instrumentation via opentelemetry-instrument
    # All required environment variables (including K8s metadata) are configured below
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

**重要**: Operatorアノテーション（`instrumentation.opentelemetry.io/inject-python`）は**コメントアウト**されています。これは二重計装を避けるためです。

これにより、以下が自動的に実行されます:
- FastAPI、LangChain、OpenAIの自動トレーシング
- 分散トレーシングの有効化
- メトリクスとログの収集
- Splunk AI Agent Monitoring対応
- リソース属性の自動付与（`service.namespace=petclinic`, `deployment.environment=o11y-custom-petclinic`）

注意: 
- 計装により、メモリとCPUのリソース使用量が増加します
- `deployment.environment` の値は `otel/user-values.yaml` の `environment` と一致させてください

### デプロイ

```bash
# GenAI Python Serviceのみデプロイ
kubectl apply -f k8s/genai-python/

# または、全サービスをデプロイ（スクリプト使用）
./scripts/deploy-services.sh
```

### デプロイ確認

```bash
# Pod状態確認
kubectl get pods -n petclinic -l app=genai-python

# ログ確認
kubectl logs -f deployment/genai-python -n petclinic

# サービス確認
kubectl get svc -n petclinic genai-python
```

## API エンドポイント

### チャットAPI（メイン）

```bash
POST /chatclient
Content-Type: text/plain

リクエストボディ: プレーンテキストのクエリ
レスポンス: プレーンテキストのレスポンス
```

**例:**

```bash
curl -X POST http://genai-python:8085/chatclient \
  -H "Content-Type: text/plain" \
  -d "List all the owners"
```

**注意**: サービス内部では8084ポートで動作していますが、Kubernetesサービスは8085ポートで公開されています。

### その他のエンドポイント

- `GET /health` - ヘルスチェック
- `GET /actuator/health` - Spring互換ヘルスチェック
- `GET /info` - サービス情報
- `POST /chat/reset` - 会話履歴のリセット

## Kong経由でのアクセス

Kong API Gatewayがデプロイされている場合、以下のパスでアクセスできます:

```bash
# パターン1: /api/genai-python/
curl -X POST http://<kong-proxy-ip>:30080/api/genai-python/chatclient \
  -H "Content-Type: text/plain" \
  -d "Show me all veterinarians"

# パターン2: /api/genai/ (同じエンドポイント)
curl -X POST http://<kong-proxy-ip>:30080/api/genai/chatclient \
  -H "Content-Type: text/plain" \
  -d "Show me all veterinarians"
```

どちらのパスも同じGenAI Python Serviceに転送されます。

## 開発

### ディレクトリ構造

```
genai-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   ├── models.py            # Pydanticモデル
│   ├── data_provider.py     # 他サービス連携
│   ├── vector_store.py      # RAG/ベクターストア
│   ├── ai_functions.py      # LangChain Tools
│   └── chat_client.py       # チャットエージェント（LangChain create_agent API使用）
├── Dockerfile               # OpenTelemetry計装をビルトイン
├── requirements.txt         # 依存パッケージ（LangChain 1.x系）
├── .dockerignore
├── build-docker.sh          # ビルドスクリプト（v1.0.0タグも作成）
└── README.md
```

### コード品質

```bash
# フォーマット
black app/

# リンター
pylint app/
flake8 app/

# 型チェック
mypy app/
```

## ライセンス

このプロジェクトはSpring PetClinicマイクロサービスのカスタマイズ版です。

## 注意事項

⚠️ このコードはAI（Cursor）によって生成されました。

- **このプロジェクトはデモンストレーション・学習目的であり、商用利用は想定していません**
- **本番環境での使用は推奨されません**
- OpenAI APIの使用には料金が発生します
- ベクターストアの初期化時に埋め込み生成が行われます（初回のみ）
- 会話履歴はメモリ内に保持され、各リクエスト後に自動クリアされます

