# app/services.py

from sqlalchemy.orm import Session
from typing import Optional
from . import models

# --- 1. LANGCHAIN IMPORTS ---
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from .database import engine # Import your SQLAlchemy engine

# --- 2. AGENT INITIALIZATION ---
# Initialize the OpenAI language model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Connect LangChain to your PostgreSQL database via the SQLAlchemy engine
db = SQLDatabase(engine)

# Create the SQL Agent. This agent is specialized for NL-to-SQL tasks.
# verbose=True lets you see the agent's "thinking" process in your terminal, which is great for debugging.
sql_agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)


# --- 3. SERVICE FUNCTIONS ---

def fetch_all_floats(db: Session, region: Optional[str] = None):
    """
    Fetches all floats, with an optional filter for the region.
    """
    print(f"SERVICE: Fetching floats. Region filter: {region}")
    query = db.query(models.Float)
    if region:
        query = query.filter(models.Float.region.ilike(f"%{region}%"))
    return query.all()

def fetch_float_timeseries(db: Session, float_id: int):
    """
    Fetches time-series data for a specific float.
    """
    print(f"SERVICE: Fetching data for float_id: {float_id}")
    return db.query(models.Measurement).filter(models.Measurement.float_id == float_id).order_by(models.Measurement.timestamp.asc()).all()

def handle_natural_language_query(query_text: str):
    """
    This function now uses the LangChain SQL agent to process the query.
    """
    print(f"SERVICE: Processing NL query: '{query_text}' with LangChain...")
    
    # Use a prompt that gives the LLM context about the schema and task
    prompt = f"""
    Based on the database schema, answer the following user question: {query_text}.
    When querying for floats, the table is called 'floats'.
    When querying for measurements, the table is called 'measurements'.
    The 'wmo_id' is the unique identifier for a float.
    """
    
    try:
        # The agent.run() method is where the magic happens!
        # It understands the prompt, writes SQL, executes it, and returns a natural language response.
        result = sql_agent_executor.invoke({"input": prompt})
        
        # The actual answer is in the 'output' key of the result dictionary
        return {"query": query_text, "response": result.get("output")}

    except Exception as e:
        # Return an error message if the agent fails
        return {"error": f"An error occurred with the LangChain agent: {e}"}