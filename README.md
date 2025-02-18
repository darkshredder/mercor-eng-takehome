# Mercor Take-Home Write-Up

## Overview
This document explains how I designed and implemented a proxy server for Mercor's take-home challenge. The goal was to manage requests from two types of clients with very different traffic patterns while keeping latency low, throughput high, and the system fair. Here's the breakdown of the client types:

- **Client A:** Sends lots of short requests in quick bursts (bursty traffic).  
- **Client B:** Sends longer requests at steady intervals (steady traffic).  

The key challenge was to process these requests efficiently while adhering to the server’s constraints.

---

## Key Constraints
1. The classification server processes up to **5 text strings per request**.
2. The processing time depends on the **square of the longest string’s length** in the batch (longer strings = longer processing).
3. Shorter strings in a batch **don’t add extra latency**.
4. The server can handle **one batch at a time**.
5. The proxy should handle batching and scheduling **transparently**, without requiring changes from clients.

---

## Design and Implementation
Here’s how I approached the problem to ensure fairness, low latency, and high throughput:

### 1. **Priority Queues for Traffic Management**
The proxy uses two separate priority queues:  
- **High-Priority Queue:** For Client A (bursty traffic).  
- **Low-Priority Queue:** For Client B (steady traffic).  

This setup ensures bursty traffic doesn’t overwhelm steady traffic and vice versa. Requests are categorized based on simple heuristics, such as string length and client behavior.

---

### 2. **Dynamic Batching for Efficiency**
- **Batch Size:** Each batch includes up to **5 requests**, maximizing server utilization.  
- **Batch Filling:** High-priority requests are processed first. If the high-priority queue has fewer than 5 requests, the remaining slots are filled with requests from the low-priority queue.  
- This ensures the server is always busy while maintaining fairness across both client types.

---

### 3. **Adaptive Sleep Intervals**
The proxy dynamically adjusts how often it checks the queues based on their size:  
- **High Traffic:** Shorter intervals to process requests faster.  
- **Low Traffic:** Longer intervals to save resources when there’s less activity.

This flexibility prevents unnecessary delays during busy periods while avoiding wasteful polling during quiet times.

---

### 4. **Retry Mechanism**
To handle potential server errors, the proxy retries failed requests up to **3 times**.  
- **Exponential Backoff:** Each retry waits progressively longer, reducing the risk of overloading the server in case of transient issues.

---

## Trade-Offs
### Fairness vs. Latency
- **Fairness:** Priority queues prevent one client type from monopolizing resources.  
- **Latency:** High-priority requests are processed faster, but low-priority requests are still handled promptly by filling batch gaps.

### Throughput vs. Complexity
- **Throughput:** The batching strategy ensures the server is used efficiently.  
- **Complexity:** A simple, heuristic-based approach keeps the implementation easy to maintain, though it could be fine-tuned further for more unpredictable traffic patterns.

---

## Room for Improvement
While the solution meets the challenge requirements, here are potential areas for enhancement:  
1. **Smarter Traffic Profiling:** Use historical data to dynamically adjust queue priorities and batch sizes.  
2. **Dynamic Batch Sizes:** Allow batch sizes to grow during high-traffic periods to boost throughput.  
3. **Rate Limiting:** Limit individual client rates to prevent resource hogging.  
4. **Request Timeouts:** Set time limits for requests to prevent clients from waiting indefinitely in case of major issues.  
5. **Monitoring and Metrics:** Add detailed logging to track latency, throughput, and fairness in real time.

---

## Metrics for Success
The implementation can be evaluated using the following metrics:  
1. **Average Latency:** How quickly requests are processed.  
2. **Tail Latency (p95/p99):** Performance of the slowest requests.  
3. **Fairness Index:** Ensures both client types get a fair share of resources.  
4. **Throughput:** How effectively the server is utilized.

---

## How to Set It Up and Test

### Step 1: Download the Code  
```bash
git clone https://github.com/darkshreddder/mercor-eng-takehome.git
cd mercor-eng-takehome
```

### Step 2: Set Up the Environment  
```bash
conda env create -f environment.yaml
conda activate mercor_takehome
```

### Step 3: Start the Classification Server  
```bash
uvicorn classification_server:app --host 0.0.0.0 --port 8001
```

### Step 4: Start the Proxy  
```bash
uvicorn proxy:app --host 0.0.0.0 --port 8000
```

### Step 5: Run the Simulation  
```bash
python simulate_clients.py
```

---

## Conclusion
This proxy server is designed to handle diverse traffic patterns by:  
- Prioritizing bursty and steady traffic effectively with **separate queues**.  
- Optimizing server usage with **dynamic batching**.  
- Ensuring robustness with **adaptive retries and sleep intervals**.  

The solution strikes a balance between fairness, latency, and throughput, making it reliable and scalable for the given scenario.