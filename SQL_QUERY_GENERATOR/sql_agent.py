from crewai import Agent, Task, Crew
from crewai.llm import LLM

# -------------------
# OLLAMA LLM
# -------------------
llm = LLM(
    model="ollama/llama3",      # IMPORTANT → use ollama/<model>
    temperature=0.0
)

# -------------------
# AGENT
# -------------------
sql_agent = Agent(
    name="SQL Generator",
    role="SQL Expert",
    backstory="You are a senior SQL developer who converts natural language into SQL queries.",
    goal="Generate correct SQL from any English text.",
    llm=llm,
    verbose=True
)

# -------------------
# TASK
# -------------------
sql_task = Task(
    description="Convert this natural language text into an SQL query: {input}",
    expected_output="Return ONLY the SQL query.",
    agent=sql_agent
)

# -------------------
# CREW
# -------------------
sql_crew = Crew(
    agents=[sql_agent],
    tasks=[sql_task],
    verbose=True
)

def generate_sql(text: str):
    """Run agent and return final SQL string."""
    result = sql_crew.kickoff(inputs={"input": text})
    return result





