# dfs-web-crawler-and-indexer
Depth-first web crawler and indexer that traverses the web as a directed graph and builds an inverted index for information retrieval.
# Web Crawler and Indexer Using Depth-First Traversal

## Overview
This project implements a **web crawler and indexer** that traverses the World Wide Web using a **depth-first search (DFS)** strategy. The system models the web as a **directed graph**, where web pages represent vertices and hyperlinks represent directed edges.

During traversal, the crawler extracts textual content from each visited page and constructs an **inverted index** compatible with a previously developed vector space search engine. The project integrates concepts from **graph traversal algorithms** and **information retrieval**, demonstrating a practical application of theoretical computer science principles.

---

## Motivation and Course Context
This assignment was developed as part of **CS 3304: Analysis of Algorithms**, where graph traversal techniques such as DFS were studied in depth. The project applies these algorithms to a real-world problem: **web crawling and indexing**.

The primary objective is to:
- Traverse web pages using DFS
- Extract and preprocess textual content
- Build an inverted index suitable for search and retrieval

---

## Algorithmic Approach

### Web as a Directed Graph
- **Vertices:** Web pages
- **Edges:** Hyperlinks between pages
- **Traversal Strategy:** Depth-First Search (DFS)

A **stack-based URL frontier** is used to ensure that each discovered path is explored fully before backtracking, consistent with classical DFS behavior.

---

## URL Frontier Control
To prevent unbounded growth and excessive memory usage:
- A strict limit of **500 URLs** is enforced
- Once the limit is reached, no additional URLs are added to the frontier

This constraint ensures computational feasibility while allowing meaningful exploration of the target website.

---

## Crawling Procedure

### Starting URL
At runtime, the crawler prompts the user to enter a starting URL in the format:

For this project, the following URL was used:
https://www.uopeople.edu/
## HTML Parsing and Text Extraction
For each visited page:
- HTML content is retrieved
- All markup, scripts, and style elements are removed
- Only **visible textual content** is retained

Tags such as `<script>` and `<style>` are explicitly excluded to prevent contamination of the indexed text. This approach follows best practices in information retrieval, where semantic content is prioritized over presentation.

---

## Text Processing Pipeline
Extracted text undergoes standard preprocessing steps:

1. **Tokenization** – splitting text into individual terms  
2. **Stop word removal** – eliminating high-frequency, low-information words  
3. **Stemming** – reducing words to root forms using the **Porter Stemmer**

These steps normalize vocabulary, reduce index size, and improve retrieval effectiveness.

---

## Inverted Index Construction
An inverted index is built during crawling, mapping:
- Each unique term
- To the documents in which it appears
- Along with term frequency information

The index format strictly follows the specifications defined in **Indexer Part 2**, ensuring **full compatibility** with the Unit 5 search engine.

---
