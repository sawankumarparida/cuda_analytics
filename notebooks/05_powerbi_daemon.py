import schedule
import time
import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from rich.console import Console
import requests

# --- SECURITY UPDATE: Import dotenv and os ---
import os
from dotenv import load_dotenv

# Load the hidden secrets from your local .env file
load_dotenv()
# ---------------------------------------------

console = Console()

# Database connection
DB_URL = 'sqlite:////mnt/c/Users/skpar/Downloads/live_market_data.db'
engine = create_engine(DB_URL)

# SECURE: Pull the URL securely from the hidden .env file!
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(message):
    """Sends a push notification straight to your Discord channel via Webhook."""
    try:
        # Failsafe if the .env file is missing
        if not DISCORD_WEBHOOK_URL:
            console.print("[bold red]❌ Error: DISCORD_WEBHOOK_URL is missing. Did you create the .env file?[/bold red]")
            return

        payload = {
            "content": message
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code in [200, 204]:  
            console.print("[bold green]💬 Discord alert sent successfully![/bold green]")
        else:
            console.print(f"[bold red]❌ Failed to send Discord alert: {response.text}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Discord network error: {e}[/bold red]")

def fetch_and_store_data():
    """Scrapes live data, calculates rolling indicators, checks signals, and pushes to SQLite."""
    console.print(f"\n[bold cyan]🔄 [{datetime.now().strftime('%H:%M:%S')}] Waking up daemon to check market signals...[/bold cyan]")
    
    try:
        tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD']
        
        # Download recent intraday data to compute rolling indicators
        df = yf.download(tickers, period='1d', interval='1m', progress=False)
        close_prices = df['Close'].dropna()
        
        latest_data = close_prices.iloc[-1:]
        latest_data = latest_data.reset_index().melt(id_vars=['Datetime'], var_name='Asset', value_name='Price_USD')
        
        # Read recent history to evaluate crossovers
        try:
            history_df = pd.read_sql("SELECT * FROM crypto_prices ORDER BY Datetime ASC", con=engine)
            full_df = pd.concat([history_df, latest_data]).drop_duplicates().tail(30)
        except Exception:
            full_df = latest_data.copy()

        # Save new row to database
        latest_data.to_sql('crypto_prices', con=engine, if_exists='append', index=False)
        
        for _, row in latest_data.iterrows():
            asset = row['Asset']
            price = row['Price_USD']
            console.print(f"  [green]✅ Inserted: {asset} -> ${price:,.2f}[/green]")
            
            # Quantitative Signal Check (EMA 5 vs SMA 20 Crossover)
            asset_history = full_df[full_df['Asset'] == asset].copy()
            if len(asset_history) >= 20:
                asset_history['EMA_5'] = asset_history['Price_USD'].ewm(span=5).mean()
                asset_history['SMA_20'] = asset_history['Price_USD'].rolling(window=20).mean()
                
                prev_row = asset_history.iloc[-2]
                curr_row = asset_history.iloc[-1]
                
                # Check for Bullish Crossover (EMA crosses above SMA)
                if prev_row['EMA_5'] <= prev_row['SMA_20'] and curr_row['EMA_5'] > curr_row['SMA_20']:
                    alert_msg = f"🚀 **BULLISH CROSSOVER ALERT!**\n• **Asset:** `{asset}`\n• **Price:** `${price:,.2f}`\n• **Signal:** Fast EMA crossed above Slow SMA!"
                    console.print(f"[bold yellow]⚡ SIGNAL TRIGGERED: {asset} Bullish Crossover![/bold yellow]")
                    send_discord_alert(alert_msg)
                
                # Check for Bearish Crossover (EMA crosses below SMA)
                elif prev_row['EMA_5'] >= prev_row['SMA_20'] and curr_row['EMA_5'] < curr_row['SMA_20']:
                    alert_msg = f"📉 **BEARISH CROSSOVER ALERT!**\n• **Asset:** `{asset}`\n• **Price:** `${price:,.2f}`\n• **Signal:** Fast EMA crossed below Slow SMA!"
                    console.print(f"[bold red]⚡ SIGNAL TRIGGERED: {asset} Bearish Crossover![/bold red]")
                    send_discord_alert(alert_msg)

        console.print("[bold yellow]💤 Going back to sleep...[/bold yellow]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error fetching data: {e}[/bold red]")

# ==========================================
# SYSTEM STARTUP 
# ==========================================
console.print("[bold magenta]🚀 Quant Alert Daemon Started![/bold magenta]")
console.print("Press [Ctrl+C] to stop the daemon.\n")

# 1. SEND STARTUP PING TO DISCORD
send_discord_alert("🟢 **SYSTEM ONLINE:** The Quant Trading Daemon has successfully started and is now monitoring live markets!")

fetch_and_store_data()
schedule.every(1).minutes.do(fetch_and_store_data)

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    console.print("\n[bold red]🛑 Daemon safely shut down by user.[/bold red]")
    # 2. SEND SHUTDOWN PING TO DISCORD
    send_discord_alert("🛑 **SYSTEM OFFLINE:** The Quant Trading Daemon has been manually shut down.")