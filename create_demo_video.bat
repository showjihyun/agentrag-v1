@echo off
echo 🎬 Agent-Builder 30-Second Demo Video Creation
echo ================================================

echo.
echo 📋 Step 1: Environment Check
echo Checking Docker services...
docker-compose ps

echo.
echo 🚀 Step 2: Starting Services
echo Starting all required services...
docker-compose up -d

echo.
echo ⏳ Step 3: Waiting for services to be ready...
timeout /t 30 /nobreak

echo.
echo 📊 Step 4: Preparing Demo Data
echo Running quick demo setup...
cd scripts
python quick_demo_setup.py
cd ..

echo.
echo 🌐 Step 5: Opening Browser
echo Opening demo URL in browser...
start http://localhost:3000/agent-builder/agentflows

echo.
echo 🎥 Step 6: Recording Instructions
echo ================================================
echo 📍 RECORDING CHECKLIST:
echo.
echo ✅ Browser Resolution: 1920x1080
echo ✅ Recording Software: OBS/Loom at 60 FPS
echo ✅ Audio: Clear microphone, no background noise
echo ✅ Duration: EXACTLY 30 seconds
echo.
echo 🎯 RECORDING SEQUENCE (30 seconds):
echo.
echo [0-3s]   Title card + transition to workflow canvas
echo [3-5s]   Drag Webhook Trigger from sidebar
echo [5-7s]   Add AI Agent (Intent Analyzer)
echo [7-9s]   Add Condition Node (3-way branching)
echo [9-11s]  Add Slack Integration
echo [11-13s] Add Email Integration
echo [13-15s] Connect all nodes with lines
echo [15-17s] Click "Test Workflow" button
echo [17-19s] Show real-time execution (nodes lighting up)
echo [19-21s] Display "✅ Completed in 3.2s"
echo [21-23s] Show metrics overlay
echo [23-25s] Transition to GitHub repository
echo [25-27s] Highlight Star button
echo [27-30s] End with "Try it yourself" call-to-action
echo.
echo 🎤 VOICEOVER SCRIPT:
echo [0-3s]   "Build AI automations with drag-and-drop simplicity."
echo [3-23s]  "Drag and drop AI agents, connect to 50+ services, execute complex workflows in seconds. No coding required."
echo [23-30s] "Star the repo and try it yourself. Get started in minutes with Docker Compose."
echo.
echo 📱 TEXT OVERLAYS TO ADD:
echo - "70+ Pre-built Nodes" (at 5s)
echo - "50+ Integrations" (at 9s)
echo - "Multi-Agent Orchestration" (at 13s)
echo - "Real-time Monitoring" (at 17s)
echo - "< 5s Execution Time" (at 19s)
echo - "⭐ Star on GitHub" (at 25s)
echo - "🐳 Docker Ready" (at 27s)
echo - "🆓 MIT License" (at 28s)
echo.
echo 🎬 Ready to record! Press any key when recording is complete...
pause

echo.
echo 📤 Step 7: Post-Recording Checklist
echo ================================================
echo ✅ Video is exactly 30.0 seconds
echo ✅ All actions completed smoothly
echo ✅ Audio is clear and synchronized
echo ✅ Text overlays are readable
echo ✅ GitHub repository link is visible
echo ✅ Call-to-action is clear
echo.
echo 🎨 EDITING GUIDELINES:
echo - Add title card: "Workflow Platform - No-Code AI Agent Builder"
echo - Use smooth fade transitions between sections
echo - Add dynamic text overlays with animations
echo - Include background music (upbeat, tech-focused)
echo - Export as MP4, 1920x1080, 30 FPS
echo.
echo 📊 SUCCESS METRICS:
echo ✅ Shows complete workflow creation in 20 seconds
echo ✅ Demonstrates real execution with 3.2s timing
echo ✅ Includes clear call-to-action
echo ✅ Maintains viewer engagement throughout
echo ✅ Conveys technical credibility
echo ✅ Optimized for social media sharing
echo.
echo 🎉 Demo video creation process complete!
echo Upload to GitHub repository and embed in README.md
echo.
pause