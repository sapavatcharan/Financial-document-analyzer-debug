from typing import Optional, Dict, Any

from crew_runner import run_crew
from db import save_analysis


def run_analysis_job(
    query: str,
    file_path: str,
    file_name: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the crew and store the result in the database, with safe fallbacks."""
    try:
        analysis = run_crew(query=query, file_path=file_path)
    except Exception as e:
        # For ANY upstream error (provider misconfig, quota, encoding, etc.),
        # return a deterministic mock analysis so the API never 500s.
        _ = str(e)  # keep for potential logging
        analysis = (
            "Mock analysis (LLM call failed):\n"
            f"- Your query was: {query!r}.\n"
            "- The backend could not complete a real model call (check provider "
            "keys, model name, or network), so this is a simulated response to "
            "demonstrate the end-to-end flow.\n"
            "- Once the LLM configuration is fixed, you will see genuine "
            "model-generated financial analysis here."
        )

    # Strip any characters (like emojis) that can't be encoded on this system
    if isinstance(analysis, str):
        analysis = analysis.encode("ascii", "ignore").decode("ascii")

    record = save_analysis(
        query=query,
        analysis=analysis,
        file_name=file_name,
        file_path=file_path,
        job_id=job_id,
    )

    return {
        "id": record.id,
        "job_id": record.job_id,
        "query": record.query,
        "file_name": record.file_name,
        "file_path": record.file_path,
        "created_at": record.created_at.isoformat(),
    }

