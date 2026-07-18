import typer
import subprocess
import os
import pandas as pd
from rich.console import Console
from rich.table import Table

# Initialize Typer app and Rich console for pretty terminal output
app = typer.Typer(help="SKP's Custom God-Mode CLI")
console = Console()

@app.command()
def update_system():
    """
    Runs a full system update for your WSL environment.
    """
    console.print("[bold cyan]🚀 Starting full system update...[/bold cyan]")
    
    # We use subprocess to run actual bash commands from inside Python
    subprocess.run(["sudo", "apt", "update"], check=True)
    subprocess.run(["sudo", "apt", "upgrade", "-y"], check=True)
    
    console.print("[bold green]✅ System update complete![/bold green]")

@app.command()
def start_project(name: str):
    """
    Generates a new project folder structure instantly.
    """
    console.print(f"[bold cyan]📁 Creating new project: {name}[/bold cyan]")
    
    os.makedirs(name, exist_ok=True)
    os.chdir(name)
    
    # Create standard files
    with open("README.md", "w") as f:
        f.write(f"# {name}\n\nProject initialized via Custom CLI.")
    
    with open("main.py", "w") as f:
        f.write('print("Hello World!")\n')
        
    console.print(f"[bold green]✅ Project '{name}' created with README and main.py![/bold green]")

@app.command()
def sync_git(message: str = typer.Option("Automated CLI sync", help="Your commit message")):
    """
    Safely adds, commits, pulls, and pushes all files to GitHub.
    """
    console.print("[bold cyan]🔄 Syncing workspace with GitHub...[/bold cyan]")
    
    try:
        # 1. Add all files
        subprocess.run(["git", "add", "."], check=True)
        # 2. Commit (check=False because it might fail if there are no changes to commit)
        subprocess.run(["git", "commit", "-m", message], check=False)
        # 3. Pull latest changes safely
        subprocess.run(["git", "pull", "origin", "main"], check=True)
        # 4. Push to cloud
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        console.print("[bold green]✅ Git sync complete! Your code is safe in the cloud.[/bold green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]❌ An error occurred during git sync.[/bold red]")

@app.command()
def analyze(file_path: str):
    """
    Instantly profiles a CSV dataset and displays key metrics in the terminal.
    """
    console.print(f"[bold cyan]📊 Analyzing {file_path}...[/bold cyan]")
    
    try:
        df = pd.read_csv(file_path)
        
        # Print Shape
        console.print(f"\n[bold green]✅ Dataset Shape:[/bold green] {df.shape[0]:,} Rows | {df.shape[1]} Columns\n")
        
        # Build the Terminal Table
        table = Table(title=f"Column Profile for {file_path}", show_header=True, header_style="bold yellow")
        table.add_column("Column Name", style="cyan", no_wrap=True)
        table.add_column("Data Type", style="magenta")
        table.add_column("Missing Values", justify="right")
        
        # Loop through columns and populate the table
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing = df[col].isna().sum()
            missing_str = f"[red]{missing}[/red]" if missing > 0 else f"[green]{missing}[/green]"
            table.add_row(col, dtype, missing_str)
            
        console.print(table)
        
    except FileNotFoundError:
        console.print(f"[bold red]❌ Error: File '{file_path}' not found.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ An error occurred: {e}[/bold red]")

if __name__ == "__main__":
    app()

