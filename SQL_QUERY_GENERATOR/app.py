from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sql_agent import generate_sql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SQL Query Generator API",
    description="API to convert natural language to SQL queries using AI",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Get all students who scored more than 90 in Math"
            }
        }

class QueryResponse(BaseModel):
    sql: str
    input_query: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SQL Query Generator",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy"}

@app.post("/generate-sql", response_model=QueryResponse)
async def generate_sql_endpoint(request: QueryRequest):
    """
    Generate SQL query from natural language input

    Args:
        request: QueryRequest containing the natural language query

    Returns:
        QueryResponse with generated SQL and original query
    """
    try:
        logger.info(f"Received query: {request.query}")
        sql = generate_sql(request.query)
        logger.info(f"Generated SQL: {sql}")

        return QueryResponse(
            sql=str(sql),
            input_query=request.query
        )
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate SQL: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




