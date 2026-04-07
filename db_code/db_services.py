"""
Package that contains all Database-related functions (excluding schema fetching, formatting and linking) used to implement the backend functionality
Author: Navid Sarwar
"""
from sqlalchemy import create_engine, text, inspect

def create_db_engine(hostname,username,password,port,databasename):
    try:
        # basic validation to ensure no empty credentials
        if None in [hostname,username,password,port,databasename]:
            return False, None
        
        # create db engine with the input credentials
        engine = create_engine(f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{databasename}", pool_pre_ping=True)

        # Try to Connect to the DB via the access credentials
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return True, engine
    
    except Exception as e:
        print(f"DB CONNECTION ERROR OCCURED {e}")
        return False,None

# Execute the provided query and return the fetched results
def execute_query(engine, query):
    with engine.connect() as conn:
        try:
            result = conn.execute(text(query))
            rows = result.mappings().all()
            return rows
            
        except Exception as e:
            return {}
        
# Execute all generated queries and return the results
def execute_all_queries(engine, formatted_queries):
    # Dict where each key is the query and its values are the returned results
    results = {}
    # Iterates through list of queries or keys of validated queries dictionary
    for query in formatted_queries:
        results[query] = execute_query(engine, query)
    
    return results

# Validate single query -> returns a dictionary containing if the query is valid and any associated error message (incase its not)
def validate_query(engine, query):
    with engine.connect() as conn:
        try:
            conn.execute(text("EXPLAIN " + str(query).strip()))
            return {"valid":True,"error":None}
        except Exception as e:
            return {"valid":False,"error":str(e)}
        
# Validate all generated queries.
# Return the list of queries as a dictionary {"query":True/False, ...} with boolean to indicate if valid
def validate_all_queries(engine, formatted_queries):
    validated_queries = {}
    for query in formatted_queries:
        validated_queries[query] = validate_query(engine, query)
    
    return validated_queries