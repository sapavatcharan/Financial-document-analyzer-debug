from crewai import Crew, Process

from agents import financial_analyst
from task import analyze_financial_document


def run_crew(query: str, file_path: str) -> str:
    """Run the main analysis crew for a given query and PDF path."""
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
    # Cast to string so it can be stored in the database easily
    return str(result)

