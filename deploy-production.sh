#!/bin/bash
#
# Deploy Lokole to Production
#
# Usage: ./deploy-production.sh
#
# This script connects to the production VM and updates the running containers
# to the latest images from Docker Hub.
#

set -e

VM_HOST="mailserver.lokole.ca"
VM_USER="opwen"

echo "🚀 Deploying Lokole to Production"
echo "=================================="
echo "Host: ${VM_USER}@${VM_HOST}"
echo ""

# Check if we can reach the VM
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes ${VM_USER}@${VM_HOST} exit 2>/dev/null; then
    echo "⚠️  Note: SSH key authentication not set up."
    echo "   You'll be prompted for password."
    echo ""
fi

ssh ${VM_USER}@${VM_HOST} "bash -s" <<'REMOTE_SCRIPT'
set -e

cd ~/lokole || { echo "❌ Failed to cd to ~/lokole"; exit 1; }

echo "📥 Pulling latest code from GitHub..."
git fetch origin --prune
git reset --hard origin/master
echo "✓ Code updated"
echo ""

echo "🐳 Pulling latest Docker images..."
docker-compose -f docker/docker-compose.prod.yml pull
echo "✓ Images pulled"
echo ""

echo "🔄 Recreating containers..."
docker-compose -f docker/docker-compose.prod.yml up -d --force-recreate
echo "✓ Containers recreated"
echo ""

echo "⏳ Waiting for containers to stabilize..."
sleep 5

echo "📊 Container Status:"
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo ""

echo "🧹 Cleaning up old images..."
docker system prune -a -f >/dev/null 2>&1 || true
echo "✓ Cleanup complete"
echo ""

echo "✅ Deployment Complete!"
REMOTE_SCRIPT

echo ""
echo "=================================="
echo "✅ Production deployment finished!"
echo ""
echo "Next steps:"
echo "  - Check logs: ssh ${VM_USER}@${VM_HOST} 'docker logs docker_api_1 --tail 50'"
echo "  - Check worker: ssh ${VM_USER}@${VM_HOST} 'docker logs docker_worker_1 --tail 50'"
echo "  - Test API: curl https://${VM_HOST}/api/healthcheck/ping"
