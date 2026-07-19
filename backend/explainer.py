import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from schemas import SecurityExplanationOutput
from state import ThreatState   


# Configure logging for production observability
logger = logging.getLogger(__name__)

def explain_security_verdict(state: ThreatState) -> Dict[str, Any]:
    """
    LangGraph node that reformats upstream security analysis into a 
    strict JSON structure for frontend ingestion without altering the verdict.
    """
    # 1. Extract necessary context from the current state
    raw_text = state.get("raw_text", "")
    semantic_verdict = state.get("semantic_verdict", "safe")
    findings = state.get("findings", [])

    # 2. Define the safe fallback response payload
    fallback_payload = {
        "summary": "Analysis complete, awaiting manual review.",
        "flagged_sections": []
    }

    try:
        # 3. Initialize the Gemini LLM
        # Using gemini-2.5-pro or gemini-2.5-flash as standard options
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,  # Zero temperature for absolute deterministic formatting
            max_retries=2
        )

        # 4. Bind the Pydantic model for structured output enforcement
        structured_llm = llm.with_structured_output(SecurityExplanationOutput)

        # 5. Construct the strict zero-shot system instructions
        system_instructions = (
            "You are an AI Security Explainer for a RAG document security pipeline.\n"
            "The document has already been analyzed by upstream systems. Do NOT perform a new analysis, "
            "and do NOT change the verdict under any circumstances.\n\n"
            "CRITICAL RULES:\n"
            "1. Generate a maximum 15-word summary explaining why the document is unsafe.\n"
            "2. Flag exact sections from the Raw Document that contributed to the verdict. Do not modify, "
            "summarize, fix typos, or rewrite the flagged text.\n"
            "3. Provide a maximum 8-word reason for each flagged section.\n"
            "4. Only use evidence explicitly provided in the Upstream Analysis. Do not invent new issues.\n"
            "5. If the Upstream Analysis indicates the document is safe, you MUST return an empty "
            "flagged_sections list and set the summary to exatamente: 'No unsafe content detected.'\n"
        )

        # 6. Assemble the user prompt containing the current pipeline state data
        user_prompt = f"""
        [Upstream Analysis Verdict]
        Verdict: {semantic_verdict}
        
        [Upstream Findings]
        {findings}
        
        [Raw Document Text]
        {raw_text}
        """

        # 7. Execute the call within a combined prompt structure
        # LangChain handles the structured parsing into the Pydantic object
        result: SecurityExplanationOutput = structured_llm.invoke([
            ("system", system_instructions),
            ("user", user_prompt)
        ])

        # 8. Convert the Pydantic model to a standard dictionary for the State
        final_payload = result.model_dump()
        
    except Exception as e:
        # Capture timeouts, API connection issues, or schema validation errors
        logger.error(f"Error in explain_security_verdict node: {str(e)}", exc_info=True)
        final_payload = fallback_payload

    # 9. Return the state update dictionary
    return {"final_explanation": final_payload}
pass
