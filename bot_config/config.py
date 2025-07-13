import sqlite3
import os
from typing import Optional, Any, Sequence

# Create an active connection to the config database. If the database cannot be opened, return None
def open_config_db_connection(file_path: str) -> sqlite3.Connection | None:
    """
    Open a connection to the config sqlite database

    Parameters:
        file_path (str): Filepath to the config database file

    Returns:
        sqlite3.Connection | None: An active sqlite connection to the specified database if it exists, otherwise None
    """
    try:
        if(os.path.exists(file_path)):
            connection: sqlite3.Connection = sqlite3.connect(file_path)
            return connection
        else:
            raise Exception(f'Database file does not exist at: {file_path}')
    except Exception as ex:
        print(f'Failed to connect to config database:\n\t{ex}')
        return None
    
# Close an active connection to the config database
def close_config_db_connection(config_connection: sqlite3.Connection) -> None:
    """
    Close a connection to the config sqlite database

    Parameters:
        config_connection (sqlite3.Connection): An active connection to the config database file
    """
    try:
        config_connection.close()
    except:
        return
    

def execute_query(config_connection: sqlite3.Connection, query: str, params: Optional[Sequence[Any]] = None, fetch_one: bool = False, fetch_all: bool = True) -> dict | list[dict] | None:
    """
    Execute a query on the config sqlite database

    Parameters:
        config_connection (sqlite3.Connection): An active connection to the config database
        query (str): The query to be executed
        params (Optional[Sequence[Any]]): Optional parameters for the query ~ Default = None
        fetch_one (bool): Should the function only fetch the first row returned from the query ~ Default = False
        fetch_all (bool): Should the function fetch all rows returned from the query ~ Default = True
    """
    config_connection.row_factory = sqlite3.Row
    cursor = config_connection.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch_one:
            row = cursor.fetchone()
            return dict(row) if row else {}

        if fetch_all:
            return [dict(row) for row in cursor.fetchall()]

        # If code reaches here, some sort of database operation was performed that needs a commit (insert, update, delete)
        config_connection.commit()
        return None
    except sqlite3.Error as ex:
        print(f'Failed to query config database:\n\t{ex}')
        return None