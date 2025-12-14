import os
import requests
import feedparser
from dotenv import load_dotenv

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
        'max_results': 10   # Fetch the top 10 most recent papers
    }

    print(f"Querying arXiv with parameters: {params}")

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()    # Raise an exception for bad status codes

        # Use feedparser to parse the XML response
        feed = feedparser.parse(response.content)

        papers_data = []
        for entry in feed.entries:
            papers_data.append({
                'title': entry.title,
                'authors': [author.name for author in entry.authors],
                'published_date': entry.published,
                'summary': entry.summary,
                'paper_url': entry.link
            })

        return papers_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from arXiv: {e}")
        return None
    
if __name__ == "__main__":
    print("Fetching latest research papers from arXiv...")
    papers = fetch_arxiv_papers()

    if papers:
        print(f"\nSuccessfully fetched {len(papers)} papers.")
        # Print details of first paper as example
        first_paper = papers[0]
        print("\n--- Example Paper ---")
        print(f"Title: {first_paper['title']}")
        print(f"Authors: {', '.join(first_paper['authors'])}")
        print(f"Published Date: {first_paper['published_date']}")
        print(f"URL: {first_paper['paper_url']}")
        print(f"Abstract: {first_paper['summary'][:300]}...")   # Print first 300 chars of summary
        print("---------------------\n")
    else:
        print("Could not fetch papers.")
