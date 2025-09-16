# app/services.py

from sqlalchemy.orm import Session, aliased
from sqlalchemy import func
from typing import Optional, List
from . import models

# (Keep the LangChain imports and agent initialization as they were)
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from .database import engine

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
db = SQLDatabase(engine, include_tables=['floats', 'profiles'])
sql_agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)


def fetch_all_floats(db: Session) -> List[dict]:
    """
    Fetches all floats and their latest known position.
    This is now a more complex query to get the last profile for each float.
    """
    print("SERVICE: Fetching all floats and their latest positions...")

    # Create a subquery to find the latest profile_time for each float
    latest_profile_sq = db.query(
        models.Profile.float_id,
        func.max(models.Profile.profile_time).label("max_time")
    ).group_by(models.Profile.float_id).subquery()

    # Main query to join floats with their latest profile
    results = db.query(
        models.Float,
        models.Profile.lat,
        models.Profile.lon
    ).join(
        latest_profile_sq,
        models.Float.float_id == latest_profile_sq.c.float_id
    ).join(
        models.Profile,
        (models.Float.float_id == models.Profile.float_id) &
        (models.Profile.profile_time == latest_profile_sq.c.max_time)
    ).all()

    # Format the response to match the FloatMetadata schema
    floats_with_location = []
    for float_obj, lat, lon in results:
        floats_with_location.append({
            "float_id": float_obj.float_id,
            "platform_number": float_obj.platform_number,
            "lat": lat,
            "lon": lon
        })
    return floats_with_location

def fetch_float_profiles(db: Session, float_id: str, variable: Optional[str] = None):
    """
    Fetches all profiles for a specific float.
    Optionally filters by a variable name (e.g., 'TEMP' or 'PSAL').
    """
    print(f"SERVICE: Fetching profiles for float_id: {float_id}, variable: {variable}")
    
    query = db.query(models.Profile).filter(models.Profile.float_id == float_id)

    if variable:
        query = query.filter(models.Profile.variable_name == variable.upper())
        
    return query.order_by(models.Profile.profile_time.asc()).all()

def handle_natural_language_query(query_text: str):
    """
    The LangChain agent will automatically adapt to the new schema,
    but the queries it generates will be more complex.
    """
    print(f"SERVICE: Processing NL query: '{query_text}' with LangChain...")
    
# In app/services.py

# ... inside the handle_natural_language_query function ...
    # In app/services.py -> handle_natural_language_query()

    prompt = f"""
    You are an expert data analyst querying a database of oceanographic ARGO float data.
    Your task is to answer the user's question by generating a final response in a specific JSON format.

    ---
    ## Schema Description:

    ### `floats` table:
    - Contains metadata for each float (`float_id`, `platform_number`, `deploy_date`, `properties` JSONB).

    ### `profiles` table:
    - Contains scientific measurements (`profile_id`, `float_id`, `profile_time`, `lat`, `lon`, `variable_name`, `variable_value`).

    ## Important Rules & Patterns:
    - **Joining:** Join on `floats.float_id = profiles.float_id`.
    - **Finding the "Latest" Data:** For questions about "current" or "last" location/measurement, find the profile with the maximum `profile_time`.
    - **Handling Vague Requests:** If the user asks a vague question like "show me everything" or "give me the data", DO NOT use UNION. Instead, provide a helpful summary and return a sample of the first 5 rows from the `floats` table.

    ---
    ## Final Output Instructions:

    You MUST format your final answer as a single JSON object with the following keys:
    1.  **`summary`**: A concise, natural-language summary of the answer.
    2.  **`visualization_hint`**: A suggestion for the frontend on how to display the data. Must be one of: "table", "map", or "timeseries".
    3.  **`data`**: The raw data results from your SQL query, formatted as a JSON array of objects.

    ---
    ## User Question:
    {query_text}
    """
    try:
        result = sql_agent_executor.invoke({"input": prompt})
        return {"query": query_text, "response": result.get("output")}
    except Exception as e:
        return {"error": f"An error occurred with the LangChain agent: {e}"}