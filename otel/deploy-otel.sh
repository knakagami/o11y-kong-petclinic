#!/bin/bash

# Deploy Splunk Distribution of OpenTelemetry Collector to Kubernetes (k3s)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$BLUE" "============================================"
print_message "$BLUE" "Splunk OTel Collector Deployment"
print_message "$BLUE" "============================================"
echo ""

# Check if user-values.yaml has been edited
if [ -f "otel/user-values.yaml" ]; then
    if grep -q "YOUR_ACCESS_TOKEN_HERE" otel/user-values.yaml; then
        print_message "$RED" "✗ user-values.yaml がまだ編集されていません。"
        echo ""
        print_message "$YELLOW" "otel/user-values.yaml を編集して以下の値を設定してください:"
        echo "  1. accessToken: Splunk Observability Cloud のアクセストークン"
        echo "  2. realm: あなたのレルム（us0, us1, eu0, jp0など）"
        echo ""
        exit 1
    fi
else
    print_message "$RED" "✗ user-values.yaml が見つかりません。"
    echo ""
    print_message "$YELLOW" "Git リポジトリから user-values.yaml が欠落している可能性があります。"
    echo "otel/user-values.yaml ファイルを作成してください。"
    echo ""
    exit 1
fi

# Check if Helm is installed
if ! command -v helm &> /dev/null; then
    print_message "$RED" "✗ Helm がインストールされていません。"
    echo "Visit: https://helm.sh/docs/intro/install/"
    exit 1
fi
print_message "$GREEN" "✓ Helm is installed"
echo ""

# Step 1: Add Splunk OTel Collector Helm repository
print_message "$YELLOW" "Step 1: Splunk OTel Collector Helm リポジトリを追加..."
helm repo add splunk-otel-collector-chart https://signalfx.github.io/splunk-otel-collector-chart 2>/dev/null || true
helm repo update
print_message "$GREEN" "✓ Helm リポジトリが追加されました"
echo ""

# Step 2: Create namespace
print_message "$YELLOW" "Step 2: splunk-otel namespace を作成..."
kubectl create namespace splunk-otel --dry-run=client -o yaml | kubectl apply -f -
print_message "$GREEN" "✓ Namespace が作成されました"
echo ""

# Step 3: Install/Upgrade Splunk OTel Collector
print_message "$YELLOW" "Step 3: Splunk OTel Collector をデプロイ..."
helm upgrade --install splunk-otel-collector \
    splunk-otel-collector-chart/splunk-otel-collector \
    --namespace splunk-otel \
    --values otel/values.yaml \
    --values otel/user-values.yaml \
    --wait \
    --timeout 10m

print_message "$GREEN" "✓ Splunk OTel Collector がデプロイされました"
echo ""

# Step 4: Wait for Pods to be ready
print_message "$YELLOW" "Splunk OTel Collector Pods の起動を待機中..."
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=splunk-otel-collector \
    -n splunk-otel \
    --timeout=300s 2>/dev/null || true
echo ""

# Step 5: Display deployment status
print_message "$GREEN" "============================================"
print_message "$GREEN" "Deployment Summary"
print_message "$GREEN" "============================================"
echo ""

print_message "$BLUE" "Splunk OTel Pods:"
kubectl get pods -n splunk-otel
echo ""

print_message "$BLUE" "Splunk OTel Services:"
kubectl get services -n splunk-otel
echo ""

print_message "$GREEN" "============================================"
print_message "$GREEN" "✓ Splunk OTel Collector デプロイ完了!"
print_message "$GREEN" "============================================"
echo ""

print_message "$YELLOW" "次のステップ:"
echo "1. Splunk Observability Cloud にログイン"
echo "2. Infrastructure Monitoring で 'petclinic-k3s' クラスターを確認"
echo "3. APM でサービスマップとトレースを確認"
echo "4. Log Observer でログを確認"
echo ""

print_message "$BLUE" "Useful commands:"
echo "  - View OTel Collector logs: kubectl logs -n splunk-otel -l app.kubernetes.io/name=splunk-otel-collector --tail=50"
echo "  - Check OTel status: kubectl get all -n splunk-otel"
echo "  - Uninstall: helm uninstall splunk-otel-collector -n splunk-otel"
echo ""

print_message "$GREEN" "Setup complete! 🎉"
echo ""

