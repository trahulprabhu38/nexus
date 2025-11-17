import json
from crewai import Agent, Task, Crew
from crewai.tools import tool

from utils.prompt_template import build_prompt
from utils.table_mapping import map_tables
from utils.llm_client import call_llm
from utils.guardrails import validate_sql


with open("schema.json", "r") as f:
    schema = json.load(f)


@tool
def generate_sql_tool(query: str):
    """Internal tool to generate SQL without external LLM."""
    tables = map_tables(query)
    prompt = build_prompt(query, schema, tables)
    sql = call_llm(prompt)
    safe, msg = validate_sql(sql)
    return {"query": query, "tables": tables, "sql": sql, "safe": safe, "message": msg}


sql_agent = Agent(
    name="SQL Generator Agent",
    role="SQL expert",
    goal="Generate SQL using internal logic",
    backstory="A tool-driven agent that does NOT call any external LLM.",
    llm=None,                       # THIS WILL NOW WORK AFTER UPDATE
    tools=[generate_sql_tool],      # Agent uses ONLY this tool
    allow_delegation=False,
    verbose=True
)


sql_task = Task(
    description="Use internal tools to generate SQL.",
    agent=sql_agent,
    expected_output="JSON containing SQL.",
    tools=[generate_sql_tool]       # force tool execution
)


sql_crew = Crew(
    agents=[sql_agent],
    tasks=[sql_task],
    verbose=True
)


def run_sql_agent(query: str):
    return sql_crew.kickoff(inputs={"query": query})


