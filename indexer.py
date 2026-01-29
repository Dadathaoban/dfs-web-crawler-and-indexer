#!/usr/bin/env python3
"""
Updated Indexer for Web Crawler Integration
Maintains same format as Indexer Part 2 for compatibility
"""

import os
import sys
import math
import pickle
from collections import defaultdict

# Add current directory to path for imports
sys.path.append('.')

try:
    from utils import *
    from stop_words import is_stop_word
    from porterstemmer import PorterStemmer
except ImportError:
    # Create minimal versions if imports fail
    print("Warning: Could not import utilities. Creating minimal versions...")
    
    import re
    import string
    
    def splitchars(s):
        return re.findall(r'[a-zA-Z0-9]+', s)
    
    def normalize_token(token):
        return token.lower().strip()
    
    def starts_with_punctuation(s):
        return s and s[0] in string.punctuation
    
    def is_number(s):
        try:
            float(s)
            return True
        except:
            try:
                int(s)
                return True
            except:
                return False
    
    def is_short(s, limit=2):
        return len(s) <= limit
    
    # Simple stop words
    STOP_WORDS = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    def is_stop_word(word):
        return word.lower() in STOP_WORDS
    
    # Simple stemmer
    class SimpleStemmer:
        def stem(self, word, start=0, end=None):
            if end is None:
                end = len(word) - 1
            return word.lower()[:end+1]

class Indexer:
    def __init__(self, corpus_path=None):
        """
        Initialize indexer.
        
        Args:
            corpus_path: Path to corpus (can be None for web crawler)
        """
        self.corpus_path = corpus_path
        
        # Try to use PorterStemmer, fallback to SimpleStemmer
        try:
            self.stemmer = PorterStemmer()
        except:
            self.stemmer = SimpleStemmer()
        
        # Data structures - MUST match Indexer Part 2 format
        self.documents = {}          # doc_path -> doc_id
        self.documents_inv = {}      # doc_id -> doc_path
        self.terms = {}              # term -> term_id
        self.terms_inv = {}          # term_id -> term
        self.postings = defaultdict(dict)  # term_id -> {doc_id: posting_data}
        self.doc_lengths = {}        # doc_id -> document vector length
        
        # Counters
        self.next_doc_id = 1
        self.next_term_id = 1
        
        # Statistics
        self.total_docs = 0
        self.total_terms = 0
        
        # For web crawler statistics
        self.stats = {
            'tokens_processed': 0,
            'stop_words_matched': 0,
            'short_words_ignored': 0,
            'numbers_ignored': 0,
            'punctuation_words_ignored': 0
        }
    
    def process_document_from_text(self, doc_content, doc_path="web_document"):
        """
        Process document text (for web crawler).
        
        Args:
            doc_content: Text content of document
            doc_path: URL or identifier for document
            
        Returns:
            doc_id: Assigned document ID
        """
        # Assign document ID
        doc_id = self.next_doc_id
        self.documents[doc_path] = doc_id
        self.documents_inv[doc_id] = doc_path
        self.next_doc_id += 1
        
        # Tokenize content
        tokens = splitchars(doc_content)
        term_freq = defaultdict(int)
        
        # Process each token
        for token in tokens:
            # Normalize
            token_lower = normalize_token(token)
            
            # Skip empty tokens
            if not token_lower:
                continue
            
            # Update statistics
            self.stats['tokens_processed'] += 1
            
            # Apply filters (same as Indexer Part 2)
            if is_stop_word(token_lower):
                self.stats['stop_words_matched'] += 1
                continue
            
            if starts_with_punctuation(token_lower):
                self.stats['punctuation_words_ignored'] += 1
                continue
            
            if is_short(token_lower):
                self.stats['short_words_ignored'] += 1
                continue
            
            if is_number(token_lower):
                self.stats['numbers_ignored'] += 1
                continue
            
            # Stem the token
            try:
                stemmed = self.stemmer.stem(token_lower, 0, len(token_lower)-1)
            except:
                stemmed = token_lower
            
            # Update term frequency
            term_freq[stemmed] += 1
        
        # Add to postings (same logic as original indexer)
        for term, freq in term_freq.items():
            if term not in self.terms:
                self.terms[term] = self.next_term_id
                self.terms_inv[self.next_term_id] = term
                self.next_term_id += 1
            
            term_id = self.terms[term]
            self.postings[term_id][doc_id] = {'tf': freq}
        
        return doc_id
    
    def build_index(self):
        """Build index from corpus files (original method)."""
        if not self.corpus_path or not os.path.exists(self.corpus_path):
            print(f"Corpus path not found: {self.corpus_path}")
            return False
        
        print(f"Building index from: {self.corpus_path}")
        
        # Get all files
        doc_files = []
        if os.path.isfile(self.corpus_path):
            doc_files = [self.corpus_path]
        elif os.path.isdir(self.corpus_path):
            for root, dirs, files in os.walk(self.corpus_path):
                for file in files:
                    if file.endswith('.txt'):
                        doc_files.append(os.path.join(root, file))
        
        print(f"Found {len(doc_files)} documents to process")
        
        # Process each document
        for i, doc_file in enumerate(doc_files, 1):
            try:
                with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                self.process_document_from_text(content, doc_file)
                print(f"Processed {i}/{len(doc_files)}: {os.path.basename(doc_file)}")
                
            except Exception as e:
                print(f"Error processing {doc_file}: {e}")
        
        # Calculate TF-IDF
        self.calculate_tf_idf()
        
        # Calculate document lengths
        self.calculate_document_lengths()
        
        # Update statistics
        self.total_docs = len(self.documents)
        self.total_terms = len(self.terms)
        
        print(f"\nIndex built successfully!")
        print(f"Documents: {self.total_docs}")
        print(f"Terms: {self.total_terms}")
        
        return True
    
    def calculate_tf_idf(self):
        """Calculate TF-IDF weights for all postings."""
        N = len(self.documents)
        
        for term_id, doc_postings in self.postings.items():
            df = len(doc_postings)
            
            if df == 0:
                continue
            
            # Calculate IDF (same formula as Indexer Part 2)
            idf = math.log(N / df) if df > 0 else 0
            
            # Update each document's TF-IDF
            for doc_id, posting in doc_postings.items():
                tf = posting['tf']
                tf_idf = tf * idf
                posting['tf_idf'] = tf_idf
                posting['idf'] = idf
                posting['df'] = df
    
    def calculate_document_lengths(self):
        """Calculate document vector lengths for cosine similarity."""
        for doc_id in self.documents_inv:
            length_squared = 0
            
            for term_id, doc_postings in self.postings.items():
                if doc_id in doc_postings:
                    tf_idf = doc_postings[doc_id]['tf_idf']
                    length_squared += tf_idf * tf_idf
            
            self.doc_lengths[doc_id] = math.sqrt(length_squared) if length_squared > 0 else 1.0
    
    def save_index(self, output_dir='.'):
        """
        Save index to files in EXACT SAME FORMAT as Indexer Part 2.
        
        Files created:
        - documents.dat: doc_path,doc_id
        - terms.dat: term,term_id  
        - postings.dat: term_id,doc_id,tf_idf,tf,idf,df
        - doc_lengths.dat: doc_id,length
        """
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save documents (same format)
            with open(os.path.join(output_dir, 'documents.dat'), 'w') as f:
                for doc_path, doc_id in self.documents.items():
                    f.write(f"{doc_path},{doc_id}\n")
            
            # Save terms (same format)
            with open(os.path.join(output_dir, 'terms.dat'), 'w') as f:
                for term, term_id in self.terms.items():
                    f.write(f"{term},{term_id}\n")
            
            # Save postings (same format with 6 decimal places for tf_idf)
            with open(os.path.join(output_dir, 'postings.dat'), 'w') as f:
                for term_id, doc_postings in self.postings.items():
                    for doc_id, posting in doc_postings.items():
                        tf_idf = posting.get('tf_idf', 0)
                        tf = posting.get('tf', 0)
                        idf = posting.get('idf', 0)
                        df = posting.get('df', 0)
                        f.write(f"{term_id},{doc_id},{tf_idf:.6f},{tf},{idf:.6f},{df}\n")
            
            # Save document lengths (same format)
            with open(os.path.join(output_dir, 'doc_lengths.dat'), 'w') as f:
                for doc_id, length in self.doc_lengths.items():
                    f.write(f"{doc_id},{length:.6f}\n")
            
            print(f"Index saved to {output_dir}/")
            return True
            
        except Exception as e:
            print(f"Error saving index: {e}")
            return False
    
    def load_index(self, input_dir='.'):
        """Load index from files (same as original)."""
        try:
            # Load documents
            self.documents = {}
            self.documents_inv = {}
            with open(os.path.join(input_dir, 'documents.dat'), 'r') as f:
                for line in f:
                    doc_path, doc_id = line.strip().split(',')
                    doc_id = int(doc_id)
                    self.documents[doc_path] = doc_id
                    self.documents_inv[doc_id] = doc_path
            
            # Load terms
            self.terms = {}
            self.terms_inv = {}
            with open(os.path.join(input_dir, 'terms.dat'), 'r') as f:
                for line in f:
                    term, term_id = line.strip().split(',')
                    term_id = int(term_id)
                    self.terms[term] = term_id
                    self.terms_inv[term_id] = term
            
            # Load postings
            from collections import defaultdict
            self.postings = defaultdict(dict)
            with open(os.path.join(input_dir, 'postings.dat'), 'r') as f:
                for line in f:
                    term_id, doc_id, tf_idf, tf, idf, df = line.strip().split(',')
                    term_id = int(term_id)
                    doc_id = int(doc_id)
                    self.postings[term_id][doc_id] = {
                        'tf_idf': float(tf_idf),
                        'tf': int(tf),
                        'idf': float(idf),
                        'df': int(df)
                    }
            
            # Load document lengths
            self.doc_lengths = {}
            with open(os.path.join(input_dir, 'doc_lengths.dat'), 'r') as f:
                for line in f:
                    doc_id, length = line.strip().split(',')
                    self.doc_lengths[int(doc_id)] = float(length)
            
            # Update counters
            self.next_doc_id = max(self.documents.values()) + 1 if self.documents else 1
            self.next_term_id = max(self.terms.values()) + 1 if self.terms else 1
            self.total_docs = len(self.documents)
            self.total_terms = len(self.terms)
            
            print(f"Index loaded successfully!")
            print(f"Documents: {self.total_docs}")
            print(f"Terms: {self.total_terms}")
            
            return True
            
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def get_statistics(self):
        """Get indexing statistics."""
        return {
            'documents': self.total_docs,
            'terms': self.total_terms,
            'tokens_processed': self.stats['tokens_processed'],
            'stop_words_matched': self.stats['stop_words_matched'],
            'short_words_ignored': self.stats['short_words_ignored'],
            'numbers_ignored': self.stats['numbers_ignored'],
            'punctuation_words_ignored': self.stats['punctuation_words_ignored']
        }

def main():
    """Main function (for standalone use)."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Indexer for Web Crawler')
    parser.add_argument('corpus_path', nargs='?', help='Path to corpus (optional for web crawler)')
    parser.add_argument('--output', '-o', default='./index_data', help='Output directory')
    parser.add_argument('--load', '-l', action='store_true', help='Load existing index')
    
    args = parser.parse_args()
    
    indexer = Indexer(args.corpus_path)
    
    if args.load:
        if indexer.load_index(args.output):
            stats = indexer.get_statistics()
            print(f"\nStatistics:")
            print(f"  Documents: {stats['documents']}")
            print(f"  Terms: {stats['terms']}")
            print(f"  Tokens processed: {stats['tokens_processed']}")
    elif args.corpus_path:
        if indexer.build_index():
            indexer.save_index(args.output)
    else:
        print("No corpus path provided. Use with web crawler.")

if __name__ == "__main__":
    main()