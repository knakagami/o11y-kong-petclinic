# Splunk Distribution of OpenTelemetry Collector

このディレクトリには、Splunk Distribution of OpenTelemetry Collector（Splunk OTel Collector）のKubernetesデプロイメント設定が含まれています。

## 📋 前提条件

- Kubernetes クラスター（k3s）が稼働していること
- `kubectl` がクラスターに接続できること
- `helm` がインストールされていること（v3.0+）
- Splunk Observability Cloud のアカウントとアクセストークン

**注意**: Helmチャートは必要な依存関係（cert-managerなど）を自動的にインストールします。事前のインストールは不要です。

## 🚀 デプロイ手順

### 簡単デプロイ（推奨）

deploy-otel.shスクリプトを使用すると、自動的にすべての手順が実行されます:

```bash
cd otel
./deploy-otel.sh
```

このスクリプトは以下を自動実行します:
- user-values.yamlの設定確認
- Helmリポジトリの追加
- Splunk OTel Collectorのデプロイ
- デプロイ状態の確認

### 手動デプロイ

手動でデプロイする場合は、以下の手順に従ってください:

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

**⚠️ 重要**: `environment` の値は、各マイクロサービスのdeployment.yamlの `deployment.environment` と統一することを推奨します。
- 現在のデフォルト値: user-values-template.yamlでは `production`、各deployment.yamlでは `o11y-custom-petclinic`
- トレースの相関を正しく行うため、これらの値を統一してください

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

**デプロイ先**: defaultネームスペース

OpenTelemetry Collectorは `default` ネームスペースにデプロイされます。これは以下の理由によります：
- OpenTelemetry Operatorが `default` ネームスペースで動作
- 各ネームスペースのPodからアクセスしやすい（`splunk-otel-collector-agent.default.svc.cluster.local`）
- クラスタ全体のメトリクス・ログ収集を一元管理

```bash
# user-values.yaml から環境固有の値を読み込んでデプロイ
helm upgrade --install splunk-otel-collector \
  splunk-otel-collector-chart/splunk-otel-collector \
  --namespace default \
  --values values.yaml \
  --values user-values.yaml \
  --wait \
  --timeout 10m
```

### 4. デプロイの確認

```bash
# Pod の状態を確認
kubectl get pods -n default -l app=splunk-otel-collector

# ログを確認
kubectl logs -n default -l app=splunk-otel-collector --tail=50

# サービスの確認
kubectl get svc -n default -l app=splunk-otel-collector
```

## 🔄 アップデート

設定を変更した後、再デプロイ：

```bash
helm upgrade splunk-otel-collector \
  splunk-otel-collector-chart/splunk-otel-collector \
  --namespace default \
  --values values.yaml \
  --values user-values.yaml
```

## 🗑️ アンインストール

```bash
# Splunk OTel Collector を削除
helm uninstall splunk-otel-collector -n default
```

## 📚 参考リンク

- [Splunk OTel Collector Helm Chart](https://github.com/signalfx/splunk-otel-collector-chart)
- [Splunk Observability Cloud ドキュメント](https://docs.splunk.com/Observability)
- [OpenTelemetry ドキュメント](https://opentelemetry.io/docs/)

## 📝 values.yaml の設定内容

[`values.yaml`](values.yaml) には環境非依存の基本設定が含まれています：

| 設定項目 | 説明 |
|---------|------|
| `gateway.enabled: false` | ゲートウェイモードを無効化（エージェントモードのみ使用） |
| `agent.enabled: true` | エージェントモード（DaemonSet）を有効化 |
| `logsCollection.containers.enabled: true` | コンテナログ収集を有効化 |
| `clusterReceiver.enabled: true` | Kubernetesメトリクス収集を有効化 |
| `operator.enabled: true` | OpenTelemetry Operatorを有効化（Java自動計装用） |
| `tolerations` | コントロールプレーンノードへのデプロイを許可 |

詳細は [`values.yaml`](values.yaml) を参照してください。

## ⚠️ 注意事項

- **このプロジェクトはデモンストレーション・学習目的であり、商用利用は想定していません**
- **本番環境での使用は推奨されません**
- **`user-values-template.yaml` をコピーして `user-values.yaml` を作成してください**
- **`user-values.yaml` はGitにコミットされません**（`.gitignore` で除外済み）
- アクセストークンは安全に管理してください
- **環境変数の統一**: `user-values.yaml` の `environment` と各deployment.yamlの `deployment.environment` を統一することを推奨

