## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import FinancialDocumentTool

## Creating a task to help solve user's query
analyze_financial_document = Task(
    description=(
        "Analyze the uploaded financial document located at: {file_path}, and answer the user's query: {query}.\n"
        "- First, use the `FinancialDocumentTool.read_data_tool` with the given file path to read the full document.\n"
        "- Identify the document type, reporting period, and key entities.\n"
        "- Extract and explain the most relevant figures, trends, and qualitative disclosures for the user's question.\n"
        "- If important information is missing or ambiguous, clearly state the limitations instead of guessing.\n"
        "- Optionally use web search to clarify general financial concepts, but never fabricate document-specific data."
    ),
    expected_output=(
        "A structured analysis in clear sections, for example:\n"
        "1) Document overview (type, period, entity).\n"
        "2) Key financial metrics and trends relevant to the query.\n"
        "3) Interpretation and insights tied directly to the user's question.\n"
        "4) Notable risks, uncertainties, and assumptions.\n"
        "5) A short, explicit disclaimer that this is not personalized financial advice."
    ),
    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

## Creating an investment analysis task
investment_analysis = Task(
    description=(
        "Using the analyzed financial document at {file_path} and the user's query: {query}, "
        "provide a high-level investment analysis.\n"
        "- Focus on fundamentals, cash flows, balance sheet strength, and qualitative disclosures.\n"
        "- Outline potential upside and downside scenarios, along with key drivers.\n"
        "- Highlight what additional information an investor would typically want before making a decision.\n"
        "- Do not ignore the user's query and do not recommend products unrelated to the document."
    ),
    expected_output=(
        "A concise, structured investment analysis that includes:\n"
        "- Summary of the issuer's financial health and business outlook.\n"
        "- Potential investment theses (bull and bear cases).\n"
        "- Key risks and sensitivity to major assumptions.\n"
        "- Clear caveats and an explicit statement that this is educational information, "
        "not individualized investment advice or a solicitation."
    ),
    agent=investment_advisor,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

## Creating a risk assessment task
risk_assessment = Task(
    description=(
        "Perform a focused risk assessment based on the financial document at {file_path} and the user's query: {query}.\n"
        "- Use the document to identify liquidity, leverage, profitability, concentration, market, and operational risks.\n"
        "- Distinguish between short-term issues and structural or long-term risks.\n"
        "- Avoid exaggeration; describe risks in balanced, evidence-based language.\n"
        "- Clearly state when the document does not provide enough information to assess a particular risk."
    ),
    expected_output=(
        "A structured risk analysis that includes:\n"
        "- Overview of the main categories of risk applicable to this entity or instrument.\n"
        "- Specific examples from the document that support each risk.\n"
        "- Possible mitigants or offsetting factors where appropriate.\n"
        "- A short summary of overall risk profile and key uncertainties."
    ),
    agent=risk_assessor,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)


verification = Task(
    description=(
        "Verify whether the file at {file_path} is a financial document and summarize its nature.\n"
        "- Use `FinancialDocumentTool.read_data_tool` to inspect the content.\n"
        "- Decide if it appears to be a financial statement, regulatory filing, investor deck, invoice, "
        "or another type of financial document.\n"
        "- If it does not appear to be financial in nature, explain why, without forcing a classification."
    ),
    expected_output=(
        "A short report that includes:\n"
        "- A binary classification: 'financial document' or 'not clearly a financial document'.\n"
        "- The inferred document type when applicable.\n"
        "- A brief explanation citing specific clues from the content.\n"
        "- Any uncertainties or limitations in the verification."
    ),
    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)