# Mercor Take-Home

## Overview

Welcome to the Mercor take-home challenge! Here’s the scenario:

You work at a company that classifies incoming text as either “code” or “not code” using a specialized server. This server accepts **up to five strings** at once, and the **processing time scales with the square of the longest string’s length**. Thanks to some batching optimizations, shorter strings in a batch don’t add to the overall latency.

Now, two customers have started using your service:

- **Customer A**: Submits large text blocks at fairly regular intervals (one big request at a time).  
- **Customer B**: Submits many short requests in quick bursts (small text snippets).

Neither customer wants to handle latency or batching logic. Your task is to build a **proxy** that receives their requests and dispatches them (in batches if you like) to the classification server.

### Key Constraints

- The server can process **only one request at a time**.
- Each request to the server can include **up to 5 strings**.
- Total request time = (max string length in the batch)², while other strings are effectively “free.”
- We want to **reduce overall latency** through intelligent batching and scheduling.
- The notion of “best latency profile” is **intentionally vague**—feel free to define and justify your own metrics (e.g., average latency, fairness, or tail latency).

## Requirements

1. **Proxy Implementation**  
   - Extend or replace the “shell” proxy in `proxy.py`.  
   - Receive traffic from two clients (simulated in `simulate_clients.py`).  
   - **Batch** requests (up to 5) and schedule them in a way that reduces latency, respecting that only one request can be processed at once.

2. **Short Write-Up**  
   - Describe your batching and scheduling approach.  
   - Discuss any trade-offs you considered (fairness vs. throughput, etc.).  
   - Suggest potential improvements if you had more time.

## Project Structure

```
.
├── environment.yaml          # Conda environment definition
├── classification_server.py # FastAPI server for classification
├── proxy.py                 # FastAPI proxy (shell implementation)
├── simulate_clients.py      # Script simulating two clients
└── README.md                # This file
```

### Classification Server (Port 8001)
- Exposes a `/classify` endpoint (FastAPI).
- Takes up to 5 text strings (`sequences`).
- Latency is **(longest string length)²**.
- Returns `"code"` or `"not code"` for each string.

### Proxy (Port 8000)
- Exposes a `/proxy_classify` endpoint (FastAPI).
- Currently just forwards each request to the server, one by one.  
- **You** will improve it to handle batching and scheduling logic.

### Client Simulation
- `simulate_clients.py` sends requests from two “clients”:  
  - **Client A**: Smaller strings, bursty rate.  
  - **Client B**: Larger strings, regular rate.  
- You can tweak their frequencies and sizes to stress-test your scheduling strategy.

## Setup Instructions

1. **Clone the Repo**
   ```bash
   git clone https://github.com/Mercor-io/mercor-eng-takehome.git
   cd mercor-eng-takehome
   ```

2. **Create the Conda Environment**
   ```bash
   conda env create -f environment.yaml
   ```
   Ensure [Conda](https://docs.conda.io/en/latest/) is installed.

3. **Activate the Environment**
   ```bash
   conda activate mercor_takehome
   ```

4. **Start the Classification Server**
   ```bash
   uvicorn classification_server:app --host 0.0.0.0 --port 8001
   ```
   Runs on `localhost:8001`.

5. **Start the Proxy (in a second terminal)**
   ```bash
   uvicorn proxy:app --host 0.0.0.0 --port 8000
   ```
   Runs on `localhost:8000`.

6. **Run the Simulation**
   ```bash
   python simulate_clients.py
   ```
   Observes how Client A and Client B interact with your proxy.

## Your Deliverable

1. **Improved `proxy.py`**  
   - Show us how you handle batching (up to 5 strings/request) and scheduling under concurrency limits.

2. **Short Write-Up**  
   - Summarize your design decisions, metrics, and improvements.

3. **Testing**  
   - We should be able to replicate your results by running the same commands above.

4. **Submission**  
   - Provide a repo link or zipped solution.  
   - Ensure everything runs smoothly in the provided Conda environment.

---

Have fun experimenting with different batching and scheduling approaches, and we look forward to seeing how you balance latency needs between these two very different clients!
