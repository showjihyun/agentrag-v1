# Agentic RAG System 시작 스크립트 (Windows PowerShell)

Write-Host "🚀 Agentic RAG System 시작 중..." -ForegroundColor Green
Write-Host ""

# 1. Docker 서비스 확인
Write-Host "📦 1단계: Docker 서비스 확인..." -ForegroundColor Cyan
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker가 실행되지 않았습니다. Docker Desktop을 시작해주세요." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker 실행 중" -ForegroundColor Green
Write-Host ""

# 2. 필수 서비스 확인
Write-Host "🔍 2단계: 필수 서비스 확인..." -ForegroundColor Cyan

# Redis 확인
$redisRunning = docker ps --filter "name=redis" --filter "status=running" --format "{{.Names}}"
if ($redisRunning) {
    Write-Host "✅ Redis 실행 중: $redisRunning" -ForegroundColor Green
} else {
    Write-Host "⚠️  Redis가 실행되지 않았습니다." -ForegroundColor Yellow
    Write-Host "   다음 명령으로 시작하세요: docker-compose up -d redis" -ForegroundColor Yellow
}

# Milvus 확인
$milvusRunning = docker ps --filter "name=milvus" --filter "status=running" --format "{{.Names}}"
if ($milvusRunning) {
    Write-Host "✅ Milvus 실행 중: $milvusRunning" -ForegroundColor Green
} else {
    Write-Host "⚠️  Milvus가 실행되지 않았습니다." -ForegroundColor Yellow
    Write-Host "   다음 명령으로 시작하세요: docker-compose up -d milvus-standalone" -ForegroundColor Yellow
}
Write-Host ""

# 3. 백엔드 확인
Write-Host "🐍 3단계: 백엔드 상태 확인..." -ForegroundColor Cyan
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 백엔드 실행 중 (http://localhost:8000)" -ForegroundColor Green
        $backendRunning = $true
    }
} catch {
    Write-Host "❌ 백엔드가 실행되지 않았습니다." -ForegroundColor Red
    Write-Host "   다음 명령으로 시작하세요:" -ForegroundColor Yellow
    Write-Host "   .\start-backend.bat" -ForegroundColor Yellow
    Write-Host "   또는:" -ForegroundColor Yellow
    Write-Host "   python -m uvicorn backend.main:app --reload --port 8000" -ForegroundColor Yellow
}
Write-Host ""

# 4. 프론트엔드 확인
Write-Host "⚛️  4단계: 프론트엔드 상태 확인..." -ForegroundColor Cyan
$frontendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 프론트엔드 실행 중 (http://localhost:3000)" -ForegroundColor Green
        $frontendRunning = $true
    }
} catch {
    Write-Host "❌ 프론트엔드가 실행되지 않았습니다." -ForegroundColor Red
    Write-Host "   다음 명령으로 시작하세요:" -ForegroundColor Yellow
    Write-Host "   cd frontend" -ForegroundColor Yellow
    Write-Host "   npm run dev" -ForegroundColor Yellow
}
Write-Host ""

# 5. 요약
Write-Host "📊 시스템 상태 요약" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "Redis:      $(if ($redisRunning) { '✅ 실행 중' } else { '❌ 중지됨' })"
Write-Host "Milvus:     $(if ($milvusRunning) { '✅ 실행 중' } else { '❌ 중지됨' })"
Write-Host "Backend:    $(if ($backendRunning) { '✅ 실행 중' } else { '❌ 중지됨' })"
Write-Host "Frontend:   $(if ($frontendRunning) { '✅ 실행 중' } else { '❌ 중지됨' })"
Write-Host ""

# 6. 다음 단계 안내
if (-not $backendRunning -or -not $frontendRunning) {
    Write-Host "🔧 다음 단계:" -ForegroundColor Yellow
    Write-Host ""
    
    if (-not $backendRunning) {
        Write-Host "백엔드 시작:" -ForegroundColor Yellow
        Write-Host "  방법 1: .\start-backend.bat" -ForegroundColor White
        Write-Host "  방법 2: python -m uvicorn backend.main:app --reload --port 8000" -ForegroundColor White
        Write-Host ""
    }
    
    if (-not $frontendRunning) {
        Write-Host "프론트엔드 시작:" -ForegroundColor Yellow
        Write-Host "  1. 새 터미널 열기" -ForegroundColor White
        Write-Host "  2. cd frontend" -ForegroundColor White
        Write-Host "  3. npm run dev" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host "🎉 모든 서비스가 정상 실행 중입니다!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 접속 URL:" -ForegroundColor Cyan
    Write-Host "  - 프론트엔드: http://localhost:3000" -ForegroundColor White
    Write-Host "  - 백엔드 API: http://localhost:8000" -ForegroundColor White
    Write-Host "  - API 문서:   http://localhost:8000/docs" -ForegroundColor White
}

Write-Host ""
Write-Host "📚 자세한 내용은 RUN_SYSTEM.md 파일을 참고하세요." -ForegroundColor Cyan
