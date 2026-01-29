#!/usr/bin/env python3
"""
HTML Parser for Web Crawler
Extracts clean text from HTML pages
"""

import re
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML, removing all tags."""
    
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore_tags = ['script', 'style', 'head', 'meta', 'link']
        self.current_tag = None
    
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()
    
    def handle_endtag(self, tag):
        self.current_tag = None
        # Add space after certain tags for better text separation
        if tag.lower() in ['p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.text.append(' ')
    
    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            cleaned = data.strip()
            if cleaned:
                self.text.append(cleaned)
    
    def get_text(self):
        """Get extracted text as a single string."""
        return ' '.join(self.text)

def extract_text_from_html(html_content):
    """
    Extract clean text from HTML content.
    
    Args:
        html_content: HTML string
        
    Returns:
        Clean text string
    """
    try:
        # Method 1: Use HTMLParser
        parser = HTMLTextExtractor()
        parser.feed(html_content)
        text = parser.get_text()
        
        # Clean up the text
        text = clean_text(text)
        
        return text
        
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        
        # Fallback: Simple regex method
        return simple_html_text_extraction(html_content)

def clean_text(text):
    """Clean extracted text."""
    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\-\'"()]', ' ', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text

def simple_html_text_extraction(html_content):
    """Simple HTML text extraction using regex (fallback method)."""
    # Remove script and style tags
    html_content = re.sub(r'<script.*?</script>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style.*?</style>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    html_content = re.sub(r'<[^>]+>', ' ', html_content)
    
    # Decode HTML entities
    html_content = html_content.replace('&nbsp;', ' ')
    html_content = html_content.replace('&amp;', '&')
    html_content = html_content.replace('&lt;', '<')
    html_content = html_content.replace('&gt;', '>')
    html_content = html_content.replace('&quot;', '"')
    html_content = html_content.replace('&#39;', "'")
    
    # Clean up text
    html_content = clean_text(html_content)
    
    return html_content

# Alternative: BeautifulSoup version (if installed)
def extract_text_with_beautifulsoup(html_content):
    """
    Extract text using BeautifulSoup (if available).
    Install with: pip install beautifulsoup4
    """
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "head", "meta", "link"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean text
        text = clean_text(text)
        
        return text
        
    except ImportError:
        print("BeautifulSoup not installed. Using built-in parser.")
        return extract_text_from_html(html_content)