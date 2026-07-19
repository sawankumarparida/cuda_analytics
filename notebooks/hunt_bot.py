import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rich.console import Console
from rich.table import Table
import os

console = Console()

def run_job_matcher():
    console.print("[bold cyan]🤖 Booting up the Ultimate Job-Hunt Bot...[/bold cyan]")
    
    # 1. Load the Scraped Data
    # This uses the CSV you generated earlier with your Job Scraper!
    csv_file = "raw_scraped_jobs.csv"
    if not os.path.exists(csv_file):
        console.print(f"[bold red]❌ Error: '{csv_file}' not found in this folder.[/bold red]")
        console.print("[yellow]Hint: Run your '01_extract_jobs.py' script first to gather data![/yellow]")
        return
        
    df = pd.read_csv(csv_file)
    
    # 2. Define Your Resume (Keywords & Skills)
    # Sourced from your uploaded business analyst.pdf
    my_resume = """
    Business Analyst, SQL Server, Python, Pandas, NumPy, R Programming, 
    Advanced Excel, Power BI, Data Visualization, Predictive Analytics, 
    Stakeholder Reporting, Generative AI, Gemini models, APIs, dashboards
    """
    console.print("[bold yellow]📄 Analyzing Resume against Job Market...[/bold yellow]")
    
    # 3. NLP Magic: TF-IDF and Cosine Similarity
    # We combine Job Title and Location to create a "document" for each job
    df['Job_Text'] = df['Job_Title'] + " " + df['Location']
    
    # Create a list of all documents: [My_Resume, Job_1, Job_2, Job_3...]
    documents = [my_resume] + df['Job_Text'].tolist()
    
    # Convert text into a mathematical matrix based on keyword importance
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Calculate how mathematically similar the Resume (index 0) is to all other jobs (index 1 to end)
    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # 4. Score and Rank the Jobs
    df['Match_Score_%'] = (similarity_scores * 100).round(2)
    
    # Sort by best match and get the top 5
    top_matches = df.sort_values(by='Match_Score_%', ascending=False).head(5)
    
    # 5. Display the Results Beautifully in the Terminal
    table = Table(title="🎯 Top 5 Best Job Matches for Your Resume", show_header=True, header_style="bold green")
    table.add_column("Match %", justify="right", style="cyan")
    table.add_column("Job Title", style="magenta")
    table.add_column("Company", style="yellow")
    table.add_column("Location", style="white")
    
    for index, row in top_matches.iterrows():
        # Highlight non-zero scores in green
        score_str = f"[bold green]{row['Match_Score_%']}%[/bold green]" if row['Match_Score_%'] > 0 else f"{row['Match_Score_%']}%"
        table.add_row(score_str, row['Job_Title'], row['Company'], row['Location'])
        
    console.print(table)
    
    # Clean up the dataframe before saving
    df = df.drop(columns=['Job_Text'])
    
    # Save the mathematically scored data
    output_filename = "scored_matched_jobs.csv"
    df.to_csv(output_filename, index=False)
    console.print(f"\n[bold green]✅ Full scored list saved to '{output_filename}'![/bold green]")

if __name__ == "__main__":
    run_job_matcher()