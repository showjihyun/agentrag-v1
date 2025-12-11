"""
부하 테스트 스크립트 (Locust)

동시접속자 5-100명을 시뮬레이션하여 시스템 성능을 테스트합니다.

사용법:
    # 설치
    pip install locust

    # 실행 (웹 UI)
    locust -f load_test.py --host=http://localhost:8000

    # 실행 (CLI)
    locust -f load_test.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless
"""

from locust import HttpUser, task, between, events
import json
import random
import time
from datetime import datetime


# 테스트용 쿼리 샘플
SAMPLE_QUERIES = [
    "머신러닝의 장점은 무엇인가요?",
    "딥러닝과 머신러닝의 차이점을 설명해주세요",
    "자연어 처리란 무엇인가요?",
    "RAG 시스템의 작동 원리를 설명해주세요",
    "벡터 데이터베이스는 어떻게 작동하나요?",
    "임베딩 모델의 역할은 무엇인가요?",
    "LLM의 한계점은 무엇인가요?",
    "프롬프트 엔지니어링 기법을 알려주세요",
    "Few-shot learning이란 무엇인가요?",
    "트랜스포머 아키텍처를 설명해주세요",
]


class RAGUser(HttpUser):
    """RAG 시스템 사용자 시뮬레이션"""

    # 사용자 간 대기 시간 (초)
    wait_time = between(2, 5)

    def on_start(self):
        """사용자 시작 시 실행"""
        self.session_id = f"load_test_{int(time.time())}_{random.randint(1000, 9999)}"
        print(f"User started with session: {self.session_id}")

    @task(5)
    def query_fast_mode(self):
        """FAST 모드 쿼리 (가장 빈번)"""
        query = random.choice(SAMPLE_QUERIES)

        with self.client.post(
            "/api/query",
            json={
                "query": query,
                "mode": "fast",
                "session_id": self.session_id,
                "top_k": 5,
            },
            catch_response=True,
            stream=True,
            name="/api/query [FAST]",
        ) as response:
            if response.status_code == 200:
                # SSE 스트림 읽기
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1

                if chunks_received > 0:
                    response.success()
                else:
                    response.failure("No chunks received")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(3)
    def query_balanced_mode(self):
        """BALANCED 모드 쿼리"""
        query = random.choice(SAMPLE_QUERIES)

        with self.client.post(
            "/api/query",
            json={
                "query": query,
                "mode": "balanced",
                "session_id": self.session_id,
                "top_k": 10,
            },
            catch_response=True,
            stream=True,
            name="/api/query [BALANCED]",
        ) as response:
            if response.status_code == 200:
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1

                if chunks_received > 0:
                    response.success()
                else:
                    response.failure("No chunks received")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def query_deep_mode(self):
        """DEEP 모드 쿼리 (가장 드물게)"""
        query = random.choice(SAMPLE_QUERIES)

        with self.client.post(
            "/api/query",
            json={
                "query": query,
                "mode": "deep",
                "session_id": self.session_id,
                "top_k": 15,
            },
            catch_response=True,
            stream=True,
            name="/api/query [DEEP]",
        ) as response:
            if response.status_code == 200:
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1

                if chunks_received > 0:
                    response.success()
                else:
                    response.failure("No chunks received")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(2)
    def health_check(self):
        """헬스 체크"""
        with self.client.get(
            "/api/health/simple", catch_response=True, name="/api/health/simple"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def get_documents(self):
        """문서 목록 조회"""
        with self.client.get(
            "/api/documents", catch_response=True, name="/api/documents"
        ) as response:
            if response.status_code in [200, 401]:  # 401은 인증 필요 (정상)
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


# 이벤트 핸들러
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """테스트 시작 시"""
    print("\n" + "=" * 60)
    print("부하 테스트 시작")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """테스트 종료 시"""
    print("\n" + "=" * 60)
    print("부하 테스트 완료")
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")


# 커스텀 테스트 시나리오
class PeakLoadUser(HttpUser):
    """피크 시간대 사용자 (더 빈번한 요청)"""

    wait_time = between(1, 3)

    def on_start(self):
        self.session_id = f"peak_test_{int(time.time())}_{random.randint(1000, 9999)}"

    @task
    def rapid_queries(self):
        """빠른 연속 쿼리"""
        for _ in range(3):
            query = random.choice(SAMPLE_QUERIES)
            self.client.post(
                "/api/query",
                json={
                    "query": query,
                    "mode": "fast",
                    "session_id": self.session_id,
                },
                stream=True,
            )
            time.sleep(0.5)


class LightLoadUser(HttpUser):
    """일반 시간대 사용자 (느린 요청)"""

    wait_time = between(5, 10)

    def on_start(self):
        self.session_id = f"light_test_{int(time.time())}_{random.randint(1000, 9999)}"

    @task
    def occasional_query(self):
        """가끔씩 쿼리"""
        query = random.choice(SAMPLE_QUERIES)
        self.client.post(
            "/api/query",
            json={"query": query, "mode": "balanced", "session_id": self.session_id},
            stream=True,
        )


if __name__ == "__main__":
    print("""
    부하 테스트 스크립트
    
    사용법:
    
    1. 웹 UI로 실행 (권장):
       locust -f load_test.py --host=http://localhost:8000
       
       브라우저에서 http://localhost:8089 접속
       - Number of users: 50 (동시 사용자 수)
       - Spawn rate: 5 (초당 증가율)
       
    2. CLI로 실행:
       locust -f load_test.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 5m --headless
       
    3. 피크 부하 테스트:
       locust -f load_test.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 10m --headless
       
    4. 가벼운 부하 테스트:
       locust -f load_test.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 3m --headless
    """)
