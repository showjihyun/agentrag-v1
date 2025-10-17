# Deployment script for Agentic RAG System (PowerShell)

Write-Host "🚀 Agentic RAG System Deployment Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if .env.production exists
if (-not (Test-Path .env.production)) {
    Write-Host "❌ Error: .env.production file not found" -ForegroundColor Red
    Write-Host "Please copy .env.production.example to .env.production and configure it" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Environment variables file found" -ForegroundColor Green
Write-Host ""

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed" -ForegroundColor Red
    exit 1
}

try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml down

# Pull latest images
Write-Host "📥 Pulling latest images..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml pull

# Build custom images
Write-Host "🔨 Building custom images..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
Write-Host "🚀 Starting services..." -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check service health
Write-Host "🏥 Checking service health..." -ForegroundColor Cyan
Write-Host ""

$services = @("postgres", "redis", "milvus", "backend", "frontend")
$allHealthy = $true

foreach ($service in $services) {
    $status = docker-compose -f docker-compose.prod.yml ps $service
    if ($status -match "healthy") {
        Write-Host "✅ $service is healthy" -ForegroundColor Green
    } else {
        Write-Host "⚠️  $service is not healthy yet" -ForegroundColor Yellow
        $allHealthy = $false
    }
}

Write-Host ""

if ($allHealthy) {
    Write-Host "🎉 Deployment successful!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some services are not healthy yet. Check logs with:" -ForegroundColor Yellow
    Write-Host "docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
}

Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps

Write-Host ""
Write-Host "🌐 Access URLs:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs: http://localhost:8000/docs" -ForegroundColor White

Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Cyan
Write-Host "  - View logs: docker-compose -f docker-compose.prod.yml logs -f" -ForegroundColor White
Write-Host "  - Stop services: docker-compose -f docker-compose.prod.yml down" -ForegroundColor White
Write-Host "  - Restart service: docker-compose -f docker-compose.prod.yml restart <service>" -ForegroundColor White
Write-Host ""
