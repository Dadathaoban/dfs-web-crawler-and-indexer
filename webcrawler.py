#!/usr/bin/env python3
"""
Web Crawler with Depth-First Search
Integrates with Indexer Part 2 for Unit 6 Assignment
"""

import sys
import os
import time
import re
import urllib.request
import urllib.parse
import urllib.error
from collections import deque
from datetime import datetime

# Import existing IR system components
sys.path.append('.')
from indexer import Indexer
from html_parser import extract_text_from_html
from url_manager import URLManager
from utils import *
from stop_words import is_stop_word
from porterstemmer import PorterStemmer

class WebCrawler:
    def __init__(self, max_urls=500, max_depth=10):
        """
        Initialize web crawler with DFS strategy.
        
        Args:
            max_urls: Maximum number of URLs in frontier (500 for assignment)
            max_depth: Maximum depth to crawl
        """
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.stemmer = PorterStemmer()
        
        # Statistics
        self.stats = {
            'documents_processed': 0,
            'total_tokens': 0,
            'unique_terms': 0,
            'stop_words_matched': 0,
            'urls_crawled': 0,
            'urls_in_frontier': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Initialize indexer
        self.indexer = Indexer(None)  # We'll process URLs, not files
        self.indexer.documents = {}
        self.indexer.postings = {}
        self.indexer.next_doc_id = 1
        self.indexer.next_term_id = 1
        
    def crawl(self, start_url):
        """
        Crawl website starting from start_url using DFS.
        
        Args:
            start_url: Starting URL (e.g., http://www.example.com)
        """
        print(f"\n{'='*80}")
        print("WEB CRAWLER - DEPTH FIRST SEARCH")
        print(f"{'='*80}")
        
        # Record start time
        self.stats['start_time'] = datetime.now()
        print(f"Start Time: {self.stats['start_time'].strftime('%H:%M')}")
        
        # Initialize URL manager
        url_manager = URLManager(max_urls=self.max_urls)
        url_manager.add_url(start_url, depth=0)
        
        print(f"\nStarting crawl from: {start_url}")
        print(f"Maximum URLs in frontier: {self.max_urls}")
        print(f"{'-'*80}")
        
        # Main crawling loop
        try:
            while not url_manager.is_empty():
                # Get next URL (DFS uses stack/LIFO)
                url, depth = url_manager.get_next_url()
                
                if depth > self.max_depth:
                    print(f"Skipping {url} - exceeded max depth {self.max_depth}")
                    continue
                
                print(f"Crawling [{self.stats['urls_crawled']+1}/{self.max_urls}]: {url}")
                
                try:
                    # Fetch webpage
                    response = self.fetch_url(url)
                    if not response:
                        continue
                    
                    # Extract text from HTML
                    html_content = response.read().decode('utf-8', errors='ignore')
                    text_content = extract_text_from_html(html_content)
                    
                    # Process document
                    self.process_document(url, text_content)
                    
                    # Extract links for DFS
                    if self.stats['urls_crawled'] < self.max_urls:
                        links = self.extract_links(html_content, url)
                        for link in links:
                            if self.stats['urls_in_frontier'] < self.max_urls:
                                url_manager.add_url(link, depth + 1)
                                self.stats['urls_in_frontier'] = url_manager.get_queue_size()
                    
                    # Update statistics
                    self.stats['urls_crawled'] += 1
                    
                    # Check if we've reached the limit
                    if self.stats['urls_crawled'] >= self.max_urls:
                        print(f"\nReached maximum URL limit: {self.max_urls}")
                        break
                        
                except Exception as e:
                    print(f"Error crawling {url}: {e}")
                    continue
                
                # Small delay to be polite
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nCrawling interrupted by user")
        
        # Record end time
        self.stats['end_time'] = datetime.now()
        
        # Calculate TF-IDF
        self.calculate_tf_idf()
        
        # Print statistics
        self.print_statistics()
        
        # Save index
        self.save_index()
        
        return self.stats
    
    def fetch_url(self, url):
        """Fetch URL content with error handling."""
        try:
            # Set headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=10)
            return response
            
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code} for {url}")
            return None
        except urllib.error.URLError as e:
            print(f"URL Error for {url}: {e.reason}")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, html_content, base_url):
        """Extract all links from HTML content."""
        links = []
        
        # Simple regex to find href attributes
        pattern = r'href=[\'"]?([^\'" >]+)'
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        
        for link in matches:
            # Skip anchors, javascript, mailto, etc.
            if link.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Make absolute URL
            absolute_url = urllib.parse.urljoin(base_url, link)
            
            # Validate URL
            if self.is_valid_url(absolute_url):
                links.append(absolute_url)
        
        return links
    
    def is_valid_url(self, url):
        """Check if URL is valid for crawling."""
        # Parse URL
        parsed = urllib.parse.urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check for common file extensions to skip
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.mp4', 
                          '.mp3', '.zip', '.tar', '.gz', '.exe', '.dmg']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        return True
    
    def process_document(self, url, text_content):
        """Process document text and add to index."""
        # Assign document ID
        doc_id = self.indexer.next_doc_id
        self.indexer.documents[url] = doc_id
        self.indexer.next_doc_id += 1
        
        # Tokenize text
        tokens = splitchars(text_content)
        term_freq = {}
        
        # Process each token
        for token in tokens:
            # Normalize
            token_lower = normalize_token(token)
            
            # Skip empty tokens
            if not token_lower:
                continue
            
            # Update total tokens count
            self.stats['total_tokens'] += 1
            
            # Check stop words
            if is_stop_word(token_lower):
                self.stats['stop_words_matched'] += 1
                continue
            
            # Skip punctuation, short words, numbers
            if starts_with_punctuation(token_lower):
                continue
            if is_short(token_lower):
                continue
            if is_number(token_lower):
                continue
            
            # Stem the token
            try:
                stemmed = self.stemmer.stem(token_lower, 0, len(token_lower)-1)
            except:
                stemmed = token_lower
            
            # Update term frequency
            if stemmed not in term_freq:
                term_freq[stemmed] = 0
            term_freq[stemmed] += 1
        
        # Add to indexer's postings
        for term, freq in term_freq.items():
            if term not in self.indexer.terms:
                self.indexer.terms[term] = self.indexer.next_term_id
                self.indexer.next_term_id += 1
                self.stats['unique_terms'] += 1
            
            term_id = self.indexer.terms[term]
            
            # Initialize postings for this term if needed
            if term_id not in self.indexer.postings:
                self.indexer.postings[term_id] = {}
            
            # Add document to term's postings
            self.indexer.postings[term_id][doc_id] = {'tf': freq}
        
        # Update document count
        self.stats['documents_processed'] += 1
    
    def calculate_tf_idf(self):
        """Calculate TF-IDF weights for all documents."""
        print("\nCalculating TF-IDF weights...")
        
        N = self.stats['documents_processed']
        
        for term_id, doc_postings in self.indexer.postings.items():
            df = len(doc_postings)
            
            if df == 0:
                continue
            
            # Calculate IDF
            idf = math.log(N / df) if df > 0 else 0
            
            # Update each document's TF-IDF
            for doc_id, posting in doc_postings.items():
                tf = posting['tf']
                tf_idf = tf * idf
                posting['tf_idf'] = tf_idf
                posting['idf'] = idf
                posting['df'] = df
        
        print("TF-IDF calculation complete.")
    
    def print_statistics(self):
        """Print crawling and indexing statistics."""
        print(f"\n{'='*80}")
        print("CRAWLING STATISTICS")
        print(f"{'='*80}")
        
        # Calculate elapsed time
        if self.stats['start_time'] and self.stats['end_time']:
            elapsed = self.stats['end_time'] - self.stats['start_time']
            hours, remainder = divmod(elapsed.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"Total time: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        print(f"Start Time: {self.stats['start_time'].strftime('%H:%M')}")
        print(f"End Time: {self.stats['end_time'].strftime('%H:%M')}")
        print(f"{'-'*80}")
        
        print(f"Documents processed: {self.stats['documents_processed']}")
        print(f"URLs crawled: {self.stats['urls_crawled']}")
        print(f"Total tokens extracted: {self.stats['total_tokens']:,}")
        print(f"Unique terms in index: {self.stats['unique_terms']:,}")
        print(f"Stop words matched: {self.stats['stop_words_matched']:,}")
        print(f"Maximum URLs in frontier: {self.max_urls}")
        
        # Calculate compression ratio
        if self.stats['total_tokens'] > 0:
            compression = (self.stats['unique_terms'] / self.stats['total_tokens']) * 100
            print(f"Vocabulary size / Total tokens: {compression:.2f}%")
        
        print(f"{'='*80}")
    
    def save_index(self):
        """Save index to disk in same format as Indexer Part 2."""
        output_dir = "./web_index"
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"\nSaving index to: {output_dir}/")
        
        # Update indexer statistics
        self.indexer.total_docs = self.stats['documents_processed']
        self.indexer.total_terms = self.stats['unique_terms']
        
        # Calculate document lengths for cosine similarity
        self.indexer.calculate_document_lengths()
        
        # Save using indexer's method
        if self.indexer.save_index(output_dir):
            print(f"Index saved successfully!")
            print(f"Files created:")
            print(f"  - {output_dir}/documents.dat")
            print(f"  - {output_dir}/terms.dat")
            print(f"  - {output_dir}/postings.dat")
            print(f"  - {output_dir}/doc_lengths.dat")
        else:
            print("Error saving index!")

def main():
    """Main function for web crawler."""
    print("\n" + "="*80)
    print("WEB CRAWLER - CS 3304 ASSIGNMENT")
    print("="*80)
    print("This web crawler:")
    print("- Uses Depth-First Search (DFS) algorithm")
    print("- Limits URL frontier to 500 URLs")
    print("- Integrates Porter Stemmer from Indexer Part 2")
    print("- Removes HTML tags and extracts clean text")
    print("- Produces same index format for Unit 5 search engine")
    print("="*80)
    
    # Get starting URL from user
    while True:
        start_url = input("\nEnter URL to crawl (must be in form http://www.domain.com): ").strip()
        
        # Basic URL validation
        if start_url.startswith(('http://', 'https://')):
            break
        else:
            print("Error: URL must start with http:// or https://")
            print("Example: http://www.example.com")
    
    # Create and run crawler
    crawler = WebCrawler(max_urls=500)
    crawler.crawl(start_url)
    
    print("\n" + "="*80)
    print("CRAWLING COMPLETE")
    print("="*80)
    print("Index saved in './web_index' directory")
    print("Use search.py to search the index: python search.py --index ./web_index")
    print("="*80)

if __name__ == "__main__":
    main()