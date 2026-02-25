# Financial Document Analyzer (CrewAI + FastAPI)

This project is a financial document analysis API built with **CrewAI** and **FastAPI**.  
It accepts uploaded PDF financial documents and a natural language query, then runs a multi-agent crew to produce a grounded, well-structured analysis.

The codebase has been debugged and hardened against hallucinations, and it now includes:

- Fixed, working CrewAI agents and tools
- Safer, goal-focused prompts
- A proper PDF reader tool
- A **synchronous API** for immediate analysis
- An **asynchronous queue-based API** using **Redis Queue (RQ)** for concurrent workloads
- A **SQLite database** for storing analysis results

---

## 1. Bugs Found and How They Were Fixed

### 1.1 Undefined LLM and Broken Agent Configuration

**Files:** `agents.py`

**Issues:**
- `llm = llm` was referencing itself and would crash at runtime.
- Agents were created with `tool=[...]` instead of `tools=[...]`.
- Agents did not consistently have access to the PDF tool or search tool.

**Fixes:**
- Properly initialized a Chat model using `langchain_openai.ChatOpenAI`, reading configuration from environment variables:

```12:22:c:\Users\chara\Downloads\financial-document-analyzer-debug\agents.py
from langchain_openai import ChatOpenAI
...
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
    temperature=0.1,
)
```

- Corrected the agents to use `tools=[...]` and wired in the appropriate tools:

```28:47:c:\Users\chara\Downloads\financial-document-analyzer-debug\agents.py
financial_analyst = Agent(
    ...
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    ...
)
```

### 1.2 Broken PDF Tool (`Pdf(...).load()` Not Defined)

**Files:** `tools.py`

**Issues:**
- The code used `Pdf(file_path=path).load()` without importing or defining `Pdf`.
- The function was declared `async` but used synchronously, causing confusion for CrewAI tooling expectations.

**Fixes:**
- Replaced the custom `Pdf` usage with `crewai_tools.FileReadTool`, providing a simple, synchronous tool callable compatible with CrewAI agents:

```6:32:c:\Users\chara\Downloads\financial-document-analyzer-debug\tools.py
from crewai_tools import FileReadTool
...
class FinancialDocumentTool:
    @staticmethod
    def read_data_tool(path: str = "data/sample.pdf") -> str:
        if not os.path.exists(path):
            raise FileNotFoundError(f"PDF file not found at path: {path}")

        reader = FileReadTool(file_path=path)
        content = reader.run()

        if isinstance(content, str):
            return "\n".join(
                line.rstrip() for line in content.splitlines() if line.strip()
            )

        return str(content)
```

### 1.3 Crew Ignored the Uploaded File Path

**Files:** `main.py`, previously

**Issues:**
- `run_crew` only passed `{'query': query}` into `.kickoff(...)`, so tasks/tools never saw the actual `file_path` of the uploaded PDF.

**Fixes:**
- Extracted crew creation into a dedicated module (`crew_runner.py`) and ensured both `query` and `file_path` are injected into the Crew:

```4:21:c:\Users\chara\Downloads\financial-document-analyzer-debug\crew_runner.py
def run_crew(query: str, file_path: str) -> str:
    financial_crew = Crew(
        agents=[financial_analyst],
        tasks=[analyze_financial_document],
        process=Process.sequential,
        verbose=True,
    )

    result = financial_crew.kickoff(
        inputs={
            "query": query,
            "file_path": file_path,
        }
    )
    return str(result)
```

### 1.4 Unsafe / Hallucination-Prone Prompts

**Files:** `agents.py`, `task.py`

**Issues:**
- Original prompts explicitly encouraged the model to:
  - Make up financial advice
  - Approve every document as “financial”
  - Invent URLs, research, and market facts
  - Ignore the user’s query

**Fixes:**
- Rewrote all agents to:
  - Be document-grounded
  - Explicitly avoid fabricating data or URLs
  - Call out uncertainty and missing information
  - Provide educational, non-personalized guidance

- Rewrote tasks to:
  - Use `{file_path}` and the PDF tool explicitly
  - Align analysis structure with real financial workflows (overview, metrics, risks, etc.)
  - Remove instructions to hallucinate or invent content.

### 1.5 Task–Agent Mismatches

**Files:** `task.py`

**Issues:**
- Verification task was incorrectly assigned to the general financial analyst.

**Fixes:**
- Properly mapped tasks to specialized agents:
  - `analyze_financial_document` → `financial_analyst`
  - `investment_analysis` → `investment_advisor`
  - `risk_assessment` → `risk_assessor`
  - `verification` → `verifier`

### 1.6 No Dependency Management or Persistence

**Files Added:** `requirements.txt`, `db.py`

**Issues:**
- No dependency file for reproducible setup.
- No database for storing analysis results.

**Fixes:**
- Created `requirements.txt` with all core dependencies (FastAPI, CrewAI, tools, Redis/RQ, SQLAlchemy).
- Implemented a simple SQLite-based persistence layer via SQLAlchemy to store every analysis result.

---

## 2. Setup Instructions

### 2.1 Prerequisites

- Python 3.10+ recommended
- `pip` for installing dependencies
- For queue-based async processing: a running **Redis** instance (e.g. `redis://localhost:6379/0`)

### 2.2 Install Dependencies

From the project root:

```bash
pip install -r requirements.txt
```

### 2.3 Environment Variables

Create a `.env` file in the project root (or set these in your environment):

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-4o-mini  # or another compatible model

# Optional: override Redis / database
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./data/analysis.db
```

### 2.4 Run the API Server (Sync + Async Endpoints)

To start the FastAPI app with Uvicorn:

```bash
python main.py
```

The API will be available at:

- Base URL: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

### 2.5 Run the Queue Worker (for Async Jobs)

In a **separate terminal**, start the RQ worker:

```bash
python worker.py
```

This worker listens on the `analysis` queue and processes background analysis jobs.

---

## 3. Usage Instructions

### 3.1 Health Check

- **Endpoint:** `GET /`
- **Description:** Verify the API is running.

**Sample Response:**

```json
{
  "message": "Financial Document Analyzer API is running"
}
```

### 3.2 Synchronous Analysis

- **Endpoint:** `POST /analyze`
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file` (required): PDF file upload.
  - `query` (optional, `Form`): Natural language question, defaults to a generic analysis query.

**Example with `curl`:**

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@/path/to/your/financial_report.pdf" \
  -F "query=What are the key risks and profitability drivers for this company?"
```

**Response (simplified):**

```json
{
  "status": "success",
  "mode": "sync",
  "query": "What are the key risks and profitability drivers for this company?",
  "analysis_id": 1,
  "analysis_metadata": {
    "id": 1,
    "job_id": null,
    "query": "What are the key risks and profitability drivers for this company?",
    "file_name": "financial_report.pdf",
    "file_path": "data/financial_document_....pdf",
    "created_at": "2026-02-25T12:34:56.789012"
  },
  "file_processed": "financial_report.pdf"
}
```

The full analysis text is stored in the database (see **Database Integration** below).

### 3.3 Asynchronous Analysis (Queue Worker Model)

- **Endpoint:** `POST /analyze/async`
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `file` (required): PDF file upload.
  - `query` (optional, `Form`): Natural language question.

**Example with `curl`:**

```bash
curl -X POST "http://localhost:8000/analyze/async" \
  -F "file=@/path/to/your/financial_report.pdf" \
  -F "query=Summarize the company performance and key risks."
```

**Response (simplified):**

```json
{
  "status": "queued",
  "mode": "async",
  "job_id": "c9c2b4e2-....-....-....-........",
  "query": "Summarize the company performance and key risks.",
  "file_saved_as": "data/financial_document_....pdf"
}
```

#### Check Job Status and Retrieve Result

- **Endpoint:** `GET /jobs/{job_id}`

**Example:**

```bash
curl "http://localhost:8000/jobs/c9c2b4e2-....-....-....-........"
```

**Response (simplified):**

```json
{
  "job_id": "c9c2b4e2-....-....-....-........",
  "status": "finished",
  "analysis": {
    "id": 2,
    "query": "Summarize the company performance and key risks.",
    "file_name": "financial_report.pdf",
    "file_path": "data/financial_document_....pdf",
    "analysis": "Full textual analysis generated by the crew...",
    "created_at": "2026-02-25T12:40:01.123456"
  }
}
```

Statuses you may see:

- `"queued"` / `"started"` / `"finished"` / `"failed"` / `"unknown"`

When `analysis` is `null`, the job is not yet completed or the record is not found.

---

## 4. Database Integration Details

**Files:** `db.py`

- Uses **SQLAlchemy** with a default SQLite database at `./data/analysis.db`.
- Table: `analysis_results`
  - `id`: integer primary key
  - `job_id`: optional, links async jobs to DB records
  - `file_name`: original uploaded file name
  - `file_path`: server-side path (for traceability)
  - `query`: user’s natural language query
  - `analysis`: full model-generated analysis (stringified)
  - `created_at`: UTC timestamp

**Key functions:**

- `save_analysis(...)`: persists one result and returns the ORM object.
- `get_analysis_by_job_id(job_id)`: retrieves the most recent result for a job.

The synchronous endpoint uses `run_analysis_job` directly (no queue, but same pipeline), while the async endpoint uses the same function via RQ workers, ensuring all analyses are stored consistently.

---

## 5. Queue Worker Model

**Files:** `main.py`, `jobs.py`, `worker.py`

- **`jobs.py`**:
  - Defines `run_analysis_job(query, file_path, file_name, job_id)` which:
    - Runs the Crew (`run_crew`)
    - Stores the result in the database (`save_analysis`)
    - Returns metadata about the stored record

- **`worker.py`**:
  - Configures a Redis connection using `REDIS_URL`
  - Listens on the `analysis` queue and processes background jobs:

```1:19:c:\Users\chara\Downloads\financial-document-analyzer-debug\worker.py
def main() -> None:
    listen = ["analysis"]
    conn = get_redis_connection()

    with Connection(conn):
        queues = [Queue(name) for name in listen]
        worker = Worker(queues)
        worker.work()
```

- **`main.py`**:
  - Provides `/analyze/async` to enqueue jobs.
  - Provides `/jobs/{job_id}` to inspect status and fetch stored analysis.

---

## 6. CrewAI-Specific Notes

- Agents and tasks are designed to:
  - Use `FinancialDocumentTool.read_data_tool` with `{file_path}` so that analyses are grounded in the actual PDF content.
  - Avoid hallucinations by:
    - Explicitly forbidding made-up numbers, entities, or URLs
    - Encouraging clear disclosure of uncertainty and missing data
  - Separate concerns between:
    - Document verification (`verifier`)
    - Core analysis (`financial_analyst`)
    - Investment narrative (`investment_advisor`)
    - Risk assessment (`risk_assessor`)

You can extend the crew (e.g., by adding new tasks that chain verification → analysis → risk) using the same patterns already in `agents.py` and `task.py`.

---

## 7. Extending the System

- **Add more document types**: Implement additional tools for Excel, CSV, or JSON financial data and plug them into new agents.
- **Advanced DB usage**: Add endpoints to list past analyses, filter by time range, user, or query text.
- **Authentication / multi-user**: Introduce user accounts and associate analyses with user IDs in the `analysis_results` table.

This structure should give you a solid, debuggable base with clear prompts, working tooling, a queue-powered async pipeline, and persistent storage for all analyses.

# Financial Document Analyzer - Debug Assignment

## Project Overview
A comprehensive financial document analysis system that processes corporate reports, financial statements, and investment documents using AI-powered analysis agents.

## Getting Started

### Install Required Libraries
```sh
pip install -r requirement.txt
```

### Sample Document
- A sample financial PDF is already provided at `data/sample.pdf` in this repo, so you can run the API immediately.
- You can replace that file with any other financial document if you prefer.
- You can also upload any financial PDF through the API endpoints (`POST /analyze` or `POST /analyze/async`).

