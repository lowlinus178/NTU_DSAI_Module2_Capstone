import os
from pydantic_settings import BaseSettings

def return_full_path(filename: str = ".env") -> str:
    absolute_path = os.path.abspath(__file__)
    directory_name = os.path.dirname(absolute_path)
    parent_directory = os.path.dirname(directory_name)
    return os.path.join(parent_directory, filename)

class Settings(BaseSettings):
    alphavantage_api_key: str
    db_name: str
    model_directory: str  # Kept as requested    
    # Ticker list from your notebook requirements
    tickers: list = ["IBM", "AAPL", "NVDA", "GOOGL", "AMZN", "SPY", "QQQ"]
    email_user: str
    email_password: str
    email_receiver: str

    class Config:
        env_file = return_full_path(".env")

settings = Settings()