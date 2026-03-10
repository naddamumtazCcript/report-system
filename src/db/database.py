"""Database connection helper"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        os.getenv('DATABASE_URL'),
        cursor_factory=RealDictCursor
    )

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(query, params)
        
        if fetch:
            result = cur.fetchall()
        else:
            result = None
        
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
