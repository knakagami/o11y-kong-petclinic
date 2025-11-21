# Splunk Distribution of OpenTelemetry Collector

このディレクトリには、Splunk Distribution of OpenTelemetry Collector（Splunk OTel Collector）のKubernetesデプロイメント設定が含まれています。

## 📋 前提条件

- Kubernetes クラスター（k3s）が稼働していること
- `kubectl` がクラスターに接続できること
- `helm` がインストールされていること（v3.0+）
- Splunk Observability Cloud のアカウントとアクセストークン

## 🔑 アクセストークンの取得

1. [Splunk Observability Cloud](https://login.signalfx.com/) にログイン
2. Settings > Access Tokens に移動
3. **New Token** をクリック
4. トークン名を入力（例: `petclinic-k3s-ingest`）
5. Scopes で **Ingest** を選択
6. **Create** をクリックしてトークンを生成
7. トークンをコピー（後で使用）

## 🚀 デプロイ手順

### 1. ユーザー設定ファイルの作成

```bash
# テンプレートから user-values.yaml を作成
cp user-values-template.yaml user-values.yaml

# 作成したファイルを編集して実際の値を入力
vi user-values.yaml
```

**必須の設定項目:**

| 項目 | 説明 |
|-----|------|
| `splunkObservability.accessToken` | Splunk Observability Cloud のアクセストークン |
| `splunkObservability.realm` | レルム（us0, us1, us2, eu0, jp0など） |
| `clusterName` | クラスター名（識別用） |
| `environment` | 環境名（production, staging, devなど） |

**オプション: Splunk Platform（Splunk Enterprise/Cloud）への送信:**

Splunk Platform にもデータを送信する場合は、`splunkPlatform` セクションを設定してください：

| 項目 | 説明 |
|-----|------|
| `splunkPlatform.token` | HEC Token（HTTP Event Collector） |
| `splunkPlatform.endpoint` | HEC Endpoint URL |
| `splunkPlatform.index` | インデックス名 |
| `splunkPlatform.insecureSkipVerify` | 自己署名証明書の検証スキップ |

### 2. Helm リポジトリの追加

```bash
# Splunk OTel Collector の Helm リポジトリを追加
helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart

# リポジトリを更新
helm repo update
```

### 3. Splunk OTel Collector のデプロイ

```bash
# user-values.yaml から環境固有の値を読み込んでデプロイ
helm upgrade --install splunk-otel-collector \
  splunk-otel-collector-chart/splunk-otel-collector \
  --namespace splunk-otel \
  --create-namespace \
  --values values.yaml \
  --values user-values.yaml \
  --wait \
  --timeout 10m
```

### 4. デプロイの確認

```bash
# Pod の状態を確認
kubectl get pods -n splunk-otel

# ログを確認
kubectl logs -n splunk-otel -l app=splunk-otel-collector --tail=50

# サービスの確認
kubectl get svc -n splunk-otel
```

## 📊 データの確認

デプロイが成功したら、以下でデータを確認できます：

### Splunk Observability Cloud

1. **Infrastructure Monitoring**
   - Kubernetes Navigator で `petclinic-k3s` クラスターを確認
   - Pod、Node、Container のメトリクスを表示

2. **APM (Application Performance Monitoring)**
   - サービスマップでマイクロサービス間の依存関係を確認
   - トレースとスパンを表示

3. **Log Observer**
   - Kubernetes ログを検索・分析
   - コンテナログとイベントを確認

### Splunk Platform（設定した場合）

Splunk Enterprise または Splunk Cloud でログデータを確認：

```spl
index="petclinic" | stats count by sourcetype
```

## 🔧 設定のカスタマイズ

### ログ収集の有効化/無効化

`values.yaml` で設定：

```yaml
logsCollection:
  enabled: true  # false で無効化
```

### クラスターレシーバーの設定

Kubernetesメトリクスとイベントの収集：

```yaml
clusterReceiver:
  enabled: true
  k8sEventsEnabled: true
```

### リソース制限の調整

必要に応じて `user-values.yaml` に追加：

```yaml
agent:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 200m
      memory: 256Mi
```

### 自動インストルメンテーション（オプション）

Java、Python、Node.js などのアプリケーションを自動的にインストルメント。
`user-values.yaml` に追加：

```yaml
operator:
  enabled: true
```

## 🔄 アップデート

設定を変更した後、再デプロイ：

```bash
helm upgrade splunk-otel-collector \
  splunk-otel-collector-chart/splunk-otel-collector \
  --namespace splunk-otel \
  --values values.yaml \
  --values user-values.yaml
```

## 🗑️ アンインストール

```bash
# Splunk OTel Collector を削除
helm uninstall splunk-otel-collector -n splunk-otel

# Namespace を削除（オプション）
kubectl delete namespace splunk-otel
```

## 📚 参考リンク

- [Splunk OTel Collector Helm Chart](https://github.com/signalfx/splunk-otel-collector-chart)
- [Splunk Observability Cloud ドキュメント](https://docs.splunk.com/Observability)
- [OpenTelemetry ドキュメント](https://opentelemetry.io/docs/)

## ⚠️ 注意事項

- **`user-values-template.yaml` をコピーして `user-values.yaml` を作成してください**
- **`user-values.yaml` はGitにコミットされません**（`.gitignore` で除外済み）
- アクセストークンは安全に管理してください
- 本番環境では、Kubernetes Secret を使用することを推奨します

## 🔐 本番環境でのシークレット管理（推奨）

Helm values に直接トークンを書く代わりに、Kubernetes Secret を使用：

```bash
# Kubernetes Secret を作成
kubectl create secret generic splunk-otel-collector \
  --from-literal=splunk_observability_access_token=YOUR_TOKEN_HERE \
  -n splunk-otel

# values.yaml で Secret を参照
# splunkObservability:
#   accessToken: ""
#   accessTokenSecret: splunk-otel-collector
```

