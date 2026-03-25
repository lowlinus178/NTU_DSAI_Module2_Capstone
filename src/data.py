import sqlite3
import pandas as pd
import requests
from src.config import settings

class AlphaVantageAPI:
    def __init__(self, api_key=settings.alphavantage_api_key):
        self.__alphavantage_api_key = api_key
  
    def get_daily(self, ticker, output_size="full"): 
        """Fetches numerical price data from AlphaVantage."""
        url = (
            "https://www.alphavantage.co/query?"
            "function=TIME_SERIES_DAILY&"
            f"symbol={ticker}&"
            f"outputsize={output_size}&"
            f"datatype=json&"
            f"apikey={self.__alphavantage_api_key}"
        )
        r = requests.get(url)
        data = r.json()
        
        if "Time Series (Daily)" not in data:
            return pd.DataFrame()
        
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index", dtype=float)
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        df.columns = [c.split(". ")[1] for c in df.columns]
        return df.reset_index()

class SQLRepository:
    def __init__(self, connection):
        self.connection = connection

    def insert_table(self, table_name, records, if_exists="replace"):
        """Saves numerical data to SQLite."""
        return records.to_sql(
            name=table_name, 
            con=self.connection, 
            if_exists=if_exists, 
            index=False
        )