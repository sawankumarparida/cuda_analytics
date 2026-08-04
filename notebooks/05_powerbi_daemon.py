import schedule
import time
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from rich.console import Console

console = Console()

# 1. Create a local SQL Database connection
# We use SQLite here because it requires zero configuration, but SQLAlchemy 
# allows you to swap this single line to connect to MS SQL Server or MySQL!
DB_URL = 'sqlite:///live_market_data.db'
engine = create_engine(DB_URL)

def fetch_and_store_data():
    """
    The core job: Scrape live data, clean it, and push to SQL.
    """
    console.print(f"\n[bold cyan]🔄 [{datetime.now().strftime('%H:%M:%S')}] Waking up daemon to fetch live data...[/bold cyan]")
    
    try:
        # Define the assets we want to track
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        
        # Download the very latest live data (last 1 day, 1-minute intervals)
        df = yf.download(tickers, period='1d', interval='1m', progress=False)
        
        # We only want the 'Close' prices
        close_prices = df['Close'].dropna()
        
        # Get the absolute most recent row of data
        latest_data = close_prices.iloc[-1:]
        
        # Clean and format the dataframe for SQL insertion
        # Melt turns it from wide format to tall format (better for Power BI)
        latest_data = latest_data.reset_index().melt(id_vars=['Datetime'], var_name='Asset', value_name='Price_USD')
        
        # Push directly to the SQL database!
        # if_exists='append' means it just adds new rows to the bottom forever
        latest_data.to_sql('crypto_prices', con=engine, if_exists='append', index=False)
        
        for _, row in latest_data.iterrows():
            console.print(f"  [green]✅ Inserted: {row['Asset']} -> ${row['Price_USD']:,.2f}[/green]")
            
        console.print("[bold yellow]💤 Going back to sleep...[/bold yellow]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error fetching data: {e}[/bold red]")

# 2. The Scheduler
# Tell the daemon how often to run the job
console.print("[bold magenta]🚀 Power BI Automation Daemon Started![/bold magenta]")
console.print("Press [Ctrl+C] to stop the daemon.\n")

# Run it immediately once so we don't have to wait
fetch_and_store_data()

# Schedule it to run every 1 minute
schedule.every(1).minutes.do(fetch_and_store_data)

# 3. The Infinite Loop
# This keeps the script running in the background forever
try:
    while True:
        schedule.run_pending()
        time.sleep(1) # Pause for 1 second to prevent maxing out the CPU
except KeyboardInterrupt:
    console.print("\n[bold red]🛑 Daemon safely shut down by user.[/bold red]")