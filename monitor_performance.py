"""
실시간 성능 모니터링 스크립트

시스템 리소스, 연결 수, 응답 시간 등을 실시간으로 모니터링합니다.

사용법:
    python monitor_performance.py
"""

import asyncio
import time
import psutil
import requests
from datetime import datetime
from typing import Dict, Any
import json


class PerformanceMonitor:
    """성능 모니터링 클래스"""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.start_time = time.time()

    def get_system_metrics(self) -> Dict[str, Any]:
        """시스템 리소스 메트릭"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_total_gb": memory.total / (1024**3),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024**3),
            "disk_total_gb": disk.total / (1024**3),
        }

    def get_docker_stats(self) -> Dict[str, Any]:
        """Docker 컨테이너 상태"""
        try:
            import docker

            client = docker.from_env()
            containers = client.containers.list()

            stats = {}
            for container in containers:
                if "agenticrag" in container.name:
                    container_stats = container.stats(stream=False)
                    cpu_delta = (
                        container_stats["cpu_stats"]["cpu_usage"]["total_usage"]
                        - container_stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    )
                    system_delta = (
                        container_stats["cpu_stats"]["system_cpu_usage"]
                        - container_stats["precpu_stats"]["system_cpu_usage"]
                    )
                    cpu_percent = (
                        (cpu_delta / system_delta)
                        * len(container_stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                        * 100.0
                    )

                    memory_usage = container_stats["memory_stats"]["usage"] / (
                        1024**2
                    )
                    memory_limit = container_stats["memory_stats"]["limit"] / (1024**2)

                    stats[container.name] = {
                        "status": container.status,
                        "cpu_percent": round(cpu_percent, 2),
                        "memory_mb": round(memory_usage, 2),
                        "memory_limit_mb": round(memory_limit, 2),
                        "memory_percent": round(
                            (memory_usage / memory_limit) * 100, 2
                        ),
                    }

            return stats
        except Exception as e:
            return {"error": str(e)}

    def get_backend_health(self) -> Dict[str, Any]:
        """백엔드 헬스 체크"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unhealthy", "error": f"Status {response.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계"""
        try:
            # PostgreSQL 연결 수
            import subprocess

            pg_result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "agenticrag-postgres",
                    "psql",
                    "-U",
                    "postgres",
                    "-d",
                    "agenticrag",
                    "-t",
                    "-c",
                    "SELECT count(*) FROM pg_stat_activity;",
                ],
                capture_output=True,
                text=True,
            )
            pg_connections = int(pg_result.stdout.strip()) if pg_result.returncode == 0 else 0

            # Redis 연결 수
            redis_result = subprocess.run(
                ["docker", "exec", "agenticrag-redis", "redis-cli", "INFO", "clients"],
                capture_output=True,
                text=True,
            )
            redis_connections = 0
            if redis_result.returncode == 0:
                for line in redis_result.stdout.split("\n"):
                    if line.startswith("connected_clients:"):
                        redis_connections = int(line.split(":")[1].strip())

            return {
                "postgres_connections": pg_connections,
                "redis_connections": redis_connections,
            }
        except Exception as e:
            return {"error": str(e)}

    def print_dashboard(self):
        """대시보드 출력"""
        uptime = time.time() - self.start_time

        print("\033[2J\033[H")  # Clear screen
        print("=" * 80)
        print(f"  RAG 시스템 성능 모니터링 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Uptime: {int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s")
        print("=" * 80)

        # 시스템 메트릭
        print("\n[시스템 리소스]")
        system = self.get_system_metrics()
        print(f"  CPU: {system['cpu_percent']:.1f}%")
        print(
            f"  Memory: {system['memory_used_gb']:.1f}GB / {system['memory_total_gb']:.1f}GB ({system['memory_percent']:.1f}%)"
        )
        print(
            f"  Disk: {system['disk_used_gb']:.1f}GB / {system['disk_total_gb']:.1f}GB ({system['disk_percent']:.1f}%)"
        )

        # 백엔드 헬스
        print("\n[백엔드 상태]")
        health = self.get_backend_health()
        if health.get("status") == "healthy":
            print(f"  Status: ✓ {health['status'].upper()}")
            if "components" in health:
                for comp_name, comp_data in health["components"].items():
                    status_icon = "✓" if comp_data.get("status") == "healthy" else "✗"
                    print(f"    {status_icon} {comp_name}: {comp_data.get('status', 'unknown')}")
        else:
            print(f"  Status: ✗ {health.get('status', 'unknown').upper()}")
            if "error" in health:
                print(f"    Error: {health['error']}")

        # 연결 통계
        print("\n[연결 통계]")
        connections = self.get_connection_stats()
        if "error" not in connections:
            print(f"  PostgreSQL: {connections['postgres_connections']} connections")
            print(f"  Redis: {connections['redis_connections']} connections")
        else:
            print(f"  Error: {connections['error']}")

        # Docker 컨테이너
        print("\n[Docker 컨테이너]")
        docker_stats = self.get_docker_stats()
        if "error" not in docker_stats:
            for name, stats in docker_stats.items():
                status_icon = "✓" if stats["status"] == "running" else "✗"
                print(f"  {status_icon} {name}")
                print(f"      CPU: {stats['cpu_percent']}%")
                print(
                    f"      Memory: {stats['memory_mb']:.0f}MB / {stats['memory_limit_mb']:.0f}MB ({stats['memory_percent']:.1f}%)"
                )
        else:
            print(f"  Docker not available: {docker_stats['error']}")

        print("\n" + "=" * 80)
        print("  Press Ctrl+C to exit")
        print("=" * 80)

    async def monitor_loop(self, interval: int = 5):
        """모니터링 루프"""
        try:
            while True:
                self.print_dashboard()
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n모니터링 종료")


async def main():
    """메인 함수"""
    print("성능 모니터링 시작...")
    print("시스템 메트릭을 수집 중...\n")

    monitor = PerformanceMonitor()
    await monitor.monitor_loop(interval=5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n프로그램 종료")
