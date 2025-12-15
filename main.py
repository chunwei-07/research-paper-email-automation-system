import os
import requests
import feedparser
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser

load_dotenv()

def fetch_arxiv_papers():
    """
    Fetches the most recent papers from arXiv based on categories defined in the .env file.
    """
    # Base URL for arXiv API
    base_url = 'http://export.arxiv.org/api/query?'

    # Get categories from environment variable and format for query
    categories = os.getenv('ARXIV_CATEGORIES', 'cs.AI').split(',')
    # Creates a search query such as: 'cat:cs.AI OR cat:cs.LG'
    search_query = ' OR '.join([f'cat:{cat.strip()}' for cat in categories])

    # Parameters for the API query
    # Sort by 'lastUpdatedDate' to get the most recent papers.
    params = {
        'search_query': search_query,
        'sortBy': 'lastUpdatedDate',
        'sortOrder': 'descending',
        'max_results': 50
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()    # Raise an exception for bad status codes

        # Use feedparser to parse the XML response
        feed = feedparser.parse(response.content)

        papers_data = []
        for entry in feed.entries:
            papers_data.append({
                'title': entry.title.replace('\n', ' '),
                'authors': [author.name for author in entry.authors],
                'published_date': entry.published,
                'summary': entry.summary.replace('\n', ' '),
                'paper_url': entry.link
            })

        return papers_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from arXiv: {e}")
        return None
    
def filter_papers(papers):
    """
    Filters papers based on:
    1. Publication date (within the last N days).
    2. Keywords (title or summary must contain at least one keyword).
    """
    filtered_papers = []

    # Get config
    keywords = os.getenv('KEYWORDS', '').lower().split(',')
    keywords = [k.strip() for k in keywords if k.strip()]

    window_days = float(os.getenv('SEARCH_WINDOW_DAYS', '1'))

    # Calculate the cutoff time (current time - window_days) in UTC
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=window_days)

    print(f"\nFiltering {len(papers)} papers...")
    print(f"- Looking for keywords: {keywords}")
    print(f"- Published after: {cutoff_date.strftime('%Y-%m-%d %H:%M UTC')}")

    for paper in papers:
        # 1. Date Check
        # arXiv dates look like '2025-01-01T12:00:00Z'. Use date_parser to handle it
        pub_date = date_parser.parse(paper['published_date'])

        if pub_date < cutoff_date:
            continue   # skip old papers

        # 2. Keyword Check
        # We check if ANY keyword exists in the Title OR the Summary
        text_to_check = (paper['title'] + " " + paper['summary']).lower()

        # Count how many keywords appear (Simple Relevance Score)
        # Could use this score to sort them later
        score = sum(1 for k in keywords if k in text_to_check)

        if score > 0:
            paper['score'] = score
            filtered_papers.append(paper)

    # Sort filtered papers by score (highest relevance first)
    filtered_papers.sort(key=lambda x: x['score'], reverse=True)
    return filtered_papers

    
if __name__ == "__main__":
    print("--- 🚀 Daily Research Paper Fetcher ---")
    
    # 1. Fetch
    raw_papers = fetch_arxiv_papers()

    if raw_papers:
        # 2. Filter
        relevant_papers = filter_papers(raw_papers)

        print(f"\n✅ Found {len(relevant_papers)} relevant papers out of {len(raw_papers)} fetched.")

        # Display top results
        for i, paper in enumerate(relevant_papers[:3], 1):
            print(f"\n{i}. [{paper['score']} matches] {paper['title']}")
            print(f"   Published: {paper['published_date']}")
            print(f"   Link: {paper['paper_url']}")

    else:
        print("No papers fetched.")
