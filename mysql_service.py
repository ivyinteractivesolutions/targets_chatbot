import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

class MySQLService:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST")
        self.user = os.getenv("MYSQL_USER")
        self.password = os.getenv("MYSQL_PASSWORD")
        self.database = os.getenv("MYSQL_DB")

    def execute_query(self, query: str):
        """Execute a SQL query and return the results as a list of dictionaries."""
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if connection.is_connected():
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query)
                result = cursor.fetchall()
                
                # Handle non-serializable types like datetime/date/decimal/timedelta
                from datetime import datetime, date, timedelta
                from decimal import Decimal
                for row in result:
                    for key, value in row.items():
                        if isinstance(value, (datetime, date)):
                            row[key] = value.isoformat()
                        elif isinstance(value, Decimal):
                            row[key] = float(value)
                        elif isinstance(value, timedelta):
                            row[key] = str(value)
                            
                return result
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return {"error": str(e)}
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

if __name__ == "__main__":
    # Quick test
    service = MySQLService()
    test_query = "SELECT 1"
    print(service.execute_query(test_query))
