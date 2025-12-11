# Performance tests using Locust

import time
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


class WorkflowUser(HttpUser):
    """Simulated user for workflow operations."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login and get auth token."""
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def list_workflows(self):
        """List all workflows (most common operation)."""
        with self.client.get(
            "/api/agent-builder/workflows",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_workflow(self):
        """Get a specific workflow."""
        workflow_id = random.randint(1, 100)
        with self.client.get(
            f"/api/agent-builder/workflows/{workflow_id}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def create_workflow(self):
        """Create a new workflow."""
        workflow_data = {
            "name": f"Load Test Workflow {random.randint(1, 10000)}",
            "description": "Performance test workflow",
            "nodes": [
                {"id": "start", "type": "start", "data": {}},
                {"id": "end", "type": "end", "data": {}}
            ],
            "edges": [{"source": "start", "target": "end"}]
        }
        
        with self.client.post(
            "/api/agent-builder/workflows",
            json=workflow_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                # Store workflow ID for later use
                self.workflow_id = response.json()["id"]
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def execute_workflow(self):
        """Execute a workflow."""
        if hasattr(self, 'workflow_id'):
            with self.client.post(
                f"/api/agent-builder/workflows/{self.workflow_id}/execute",
                json={"input_data": {"test": "data"}},
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")


class QueryUser(HttpUser):
    """Simulated user for RAG query operations."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login and get auth token."""
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(5)
    def fast_query(self):
        """Fast mode query (most common)."""
        queries = [
            "What is RAG?",
            "How does it work?",
            "Tell me about AI",
            "Explain machine learning",
            "What is deep learning?"
        ]
        
        query_data = {
            "query": random.choice(queries),
            "mode": "fast"
        }
        
        with self.client.post(
            "/api/query",
            json=query_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def balanced_query(self):
        """Balanced mode query."""
        query_data = {
            "query": "Explain the architecture of RAG systems",
            "mode": "balanced"
        }
        
        with self.client.post(
            "/api/query",
            json=query_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def deep_query(self):
        """Deep mode query (least common, most expensive)."""
        query_data = {
            "query": "Provide a comprehensive analysis of multi-agent RAG systems",
            "mode": "deep"
        }
        
        with self.client.post(
            "/api/query",
            json=query_data,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


# Performance metrics collection
response_times = []
error_count = 0
success_count = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Collect performance metrics."""
    global response_times, error_count, success_count
    
    response_times.append(response_time)
    
    if exception:
        error_count += 1
    else:
        success_count += 1


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print performance summary."""
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print("\n" + "="*50)
        print("PERFORMANCE TEST SUMMARY")
        print("="*50)
        print(f"Total Requests: {len(response_times)}")
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
        print(f"Success Rate: {success_count / len(response_times) * 100:.2f}%")
        print(f"\nResponse Times (ms):")
        print(f"  Average: {avg_response_time:.2f}")
        print(f"  Min: {min_response_time:.2f}")
        print(f"  Max: {max_response_time:.2f}")
        print(f"  P50: {p50:.2f}")
        print(f"  P95: {p95:.2f}")
        print(f"  P99: {p99:.2f}")
        print("="*50 + "\n")


# Usage:
# locust -f backend/tests/performance/test_performance.py --host=http://localhost:8000
# 
# For headless mode:
# locust -f backend/tests/performance/test_performance.py --host=http://localhost:8000 \
#        --users 100 --spawn-rate 10 --run-time 5m --headless
