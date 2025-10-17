/**
 * E2E Test: Performance Benchmarks
 * 
 * Automated performance testing with P50/P95/P99 latency tracking
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

interface PerformanceMetric {
  testName: string;
  timestamp: string;
  latency: number;
  mode: string;
  complexity: string;
}

interface BenchmarkResults {
  p50: number;
  p95: number;
  p99: number;
  mean: number;
  min: number;
  max: number;
  samples: number;
}

class PerformanceBenchmark {
  private metrics: PerformanceMetric[] = [];
  private resultsDir = path.join(process.cwd(), 'tests', 'performance-results');

  constructor() {
    if (!fs.existsSync(this.resultsDir)) {
      fs.mkdirSync(this.resultsDir, { recursive: true });
    }
  }

  recordMetric(metric: PerformanceMetric) {
    this.metrics.push(metric);
  }

  calculatePercentile(values: number[], percentile: number): number {
    const sorted = values.slice().sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[Math.max(0, index)];
  }

  analyze(): BenchmarkResults {
    const latencies = this.metrics.map(m => m.latency);
    
    return {
      p50: this.calculatePercentile(latencies, 50),
      p95: this.calculatePercentile(latencies, 95),
      p99: this.calculatePercentile(latencies, 99),
      mean: latencies.reduce((a, b) => a + b, 0) / latencies.length,
      min: Math.min(...latencies),
      max: Math.max(...latencies),
      samples: latencies.length
    };
  }

  saveResults() {
    const results = this.analyze();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `benchmark-${timestamp}.json`;
    
    const report = {
      timestamp: new Date().toISOString(),
      summary: results,
      metrics: this.metrics
    };
    
    fs.writeFileSync(
      path.join(this.resultsDir, filename),
      JSON.stringify(report, null, 2)
    );
    
    // Also update latest results
    fs.writeFileSync(
      path.join(this.resultsDir, 'latest.json'),
      JSON.stringify(report, null, 2)
    );
    
    return results;
  }

  detectRegression(threshold: number = 1.2): boolean {
    const latestFile = path.join(this.resultsDir, 'latest.json');
    const previousFile = path.join(this.resultsDir, 'previous.json');
    
    if (!fs.existsSync(previousFile)) {
      // No previous results to compare
      return false;
    }
    
    const current = this.analyze();
    const previous = JSON.parse(fs.readFileSync(previousFile, 'utf-8')).summary;
    
    // Check if P95 latency increased by more than threshold
    const regression = current.p95 > previous.p95 * threshold;
    
    if (regression) {
      console.warn(`⚠️  Performance regression detected!`);
      console.warn(`   Previous P95: ${previous.p95.toFixed(2)}ms`);
      console.warn(`   Current P95: ${current.p95.toFixed(2)}ms`);
      console.warn(`   Increase: ${((current.p95 / previous.p95 - 1) * 100).toFixed(1)}%`);
    }
    
    return regression;
  }
}

test.describe('Performance Benchmarks', () => {
  let benchmark: PerformanceBenchmark;

  test.beforeAll(() => {
    benchmark = new PerformanceBenchmark();
  });

  test.afterAll(() => {
    const results = benchmark.saveResults();
    
    console.log('\n📊 Performance Benchmark Results:');
    console.log(`   P50 (median): ${results.p50.toFixed(2)}ms`);
    console.log(`   P95: ${results.p95.toFixed(2)}ms`);
    console.log(`   P99: ${results.p99.toFixed(2)}ms`);
    console.log(`   Mean: ${results.mean.toFixed(2)}ms`);
    console.log(`   Min: ${results.min.toFixed(2)}ms`);
    console.log(`   Max: ${results.max.toFixed(2)}ms`);
    console.log(`   Samples: ${results.samples}`);
    
    // Check for regression
    const hasRegression = benchmark.detectRegression();
    if (hasRegression) {
      console.warn('\n⚠️  Performance regression detected! Review recent changes.');
    }
  });

  test('benchmark fast mode queries (10 samples)', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const queries = [
      'What is AI?',
      'Define machine learning',
      'Explain neural networks',
      'What is deep learning?',
      'Define NLP',
      'What is computer vision?',
      'Explain reinforcement learning',
      'What is supervised learning?',
      'Define unsupervised learning',
      'What is transfer learning?'
    ];
    
    for (const query of queries) {
      // Clear previous messages
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      // Measure query latency
      const startTime = Date.now();
      
      await page.locator('input[placeholder*="Ask a question"]').fill(query);
      await page.locator('button[type="submit"]').click();
      
      // Wait for response
      await page.waitForSelector('[role="article"]', { timeout: 10000 });
      await expect(page.locator('text=Complete')).toBeVisible({ timeout: 5000 });
      
      const endTime = Date.now();
      const latency = endTime - startTime;
      
      benchmark.recordMetric({
        testName: 'fast-mode-query',
        timestamp: new Date().toISOString(),
        latency,
        mode: 'fast',
        complexity: 'simple'
      });
      
      // Verify response time is reasonable for fast mode
      expect(latency).toBeLessThan(5000); // Should be under 5 seconds
    }
  });

  test('benchmark balanced mode queries (5 samples)', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const queries = [
      'Compare AI and machine learning',
      'Explain the differences between supervised and unsupervised learning',
      'How do neural networks work in detail?',
      'What are the applications of deep learning?',
      'Describe the evolution of natural language processing'
    ];
    
    for (const query of queries) {
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      const startTime = Date.now();
      
      await page.locator('input[placeholder*="Ask a question"]').fill(query);
      
      // Select balanced mode if not auto-selected
      const balancedButton = page.locator('button:has-text("Balanced")');
      if (await balancedButton.isVisible()) {
        await balancedButton.click();
      }
      
      await page.locator('button[type="submit"]').click();
      
      // Wait for preliminary response
      await page.waitForSelector('[role="article"]', { timeout: 5000 });
      
      // Wait for final response
      await expect(page.locator('text=Complete')).toBeVisible({ timeout: 15000 });
      
      const endTime = Date.now();
      const latency = endTime - startTime;
      
      benchmark.recordMetric({
        testName: 'balanced-mode-query',
        timestamp: new Date().toISOString(),
        latency,
        mode: 'balanced',
        complexity: 'medium'
      });
      
      // Balanced mode should be under 15 seconds
      expect(latency).toBeLessThan(15000);
    }
  });

  test('benchmark deep mode queries (3 samples)', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const queries = [
      'Provide a comprehensive analysis of artificial intelligence and its impact on society',
      'Explain the mathematical foundations of neural networks and backpropagation',
      'Compare different machine learning architectures and their use cases'
    ];
    
    for (const query of queries) {
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      const startTime = Date.now();
      
      await page.locator('input[placeholder*="Ask a question"]').fill(query);
      
      // Select deep mode
      const deepButton = page.locator('button:has-text("Deep")');
      if (await deepButton.isVisible()) {
        await deepButton.click();
      }
      
      await page.locator('button[type="submit"]').click();
      
      // Wait for response (deep mode takes longer)
      await page.waitForSelector('[role="article"]', { timeout: 10000 });
      await expect(page.locator('text=Complete')).toBeVisible({ timeout: 30000 });
      
      const endTime = Date.now();
      const latency = endTime - startTime;
      
      benchmark.recordMetric({
        testName: 'deep-mode-query',
        timestamp: new Date().toISOString(),
        latency,
        mode: 'deep',
        complexity: 'complex'
      });
      
      // Deep mode should be under 30 seconds
      expect(latency).toBeLessThan(30000);
    }
  });

  test('benchmark document upload performance', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const fileSizes = [
      { name: 'small.txt', size: 1024 }, // 1KB
      { name: 'medium.txt', size: 10240 }, // 10KB
      { name: 'large.txt', size: 102400 } // 100KB
    ];
    
    for (const fileSpec of fileSizes) {
      const fileInput = page.locator('input[type="file"]');
      
      if (await fileInput.isVisible()) {
        const startTime = Date.now();
        
        // Create file with specified size
        const content = 'A'.repeat(fileSpec.size);
        await fileInput.setInputFiles({
          name: fileSpec.name,
          mimeType: 'text/plain',
          buffer: Buffer.from(content)
        });
        
        // Wait for upload completion
        await expect(page.locator('text=/uploaded|success/i')).toBeVisible({ timeout: 15000 });
        
        const endTime = Date.now();
        const latency = endTime - startTime;
        
        benchmark.recordMetric({
          testName: 'document-upload',
          timestamp: new Date().toISOString(),
          latency,
          mode: 'upload',
          complexity: fileSpec.name
        });
      }
    }
  });
});
