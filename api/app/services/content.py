"""
Content processing - Linus style: Transform data, don't complicate it.
"Good taste: eliminating edge cases by making them normal cases."
"""

import hashlib
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Process content - no strategies, no adapters, just functions"""
    
    @staticmethod
    def extract_text(html: str) -> str:
        """Extract text from HTML - simple regex, good enough"""
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean whitespace
        text = ' '.join(text.split())
        return text
    
    @staticmethod
    def generate_hash(content: str) -> str:
        """Generate content hash - for deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def summarize(text: str, max_length: int = 200) -> str:
        """Simple summarization - first N characters of sentences"""
        if len(text) <= max_length:
            return text
        
        # Find sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        summary = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(summary) + len(sentence) > max_length:
                break
            
            summary += sentence + ". "
        
        return summary.strip() or text[:max_length] + "..."
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords - simple word frequency"""
        # Common words to ignore
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                    'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'}
        
        # Tokenize and count
        words = re.findall(r'\b[a-z]+\b', text.lower())
        word_freq = {}
        
        for word in words:
            if len(word) > 3 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]


def process_item(raw_content: Dict[str, Any]) -> Dict[str, Any]:
    """Process a content item - one function, clear flow"""
    processor = ContentProcessor()
    
    # Extract basic fields - with defaults
    title = raw_content.get('title', 'Untitled')
    url = raw_content.get('url', '')
    published = raw_content.get('published', datetime.now())
    
    # Process content
    raw_text = raw_content.get('content', '')
    if raw_content.get('is_html'):
        text = processor.extract_text(raw_text)
    else:
        text = raw_text
    
    # Generate derived fields
    content_hash = processor.generate_hash(text)
    summary = processor.summarize(text)
    keywords = processor.extract_keywords(text)
    
    return {
        'title': title,
        'url': url,
        'content': text,
        'summary': summary,
        'keywords': keywords,
        'content_hash': content_hash,
        'published_at': published,
        'processed_at': datetime.now()
    }


def batch_process(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process multiple items - no parallelism complexity"""
    processed = []
    seen_hashes = set()
    
    for item in items:
        try:
            result = process_item(item)
            
            # Simple deduplication
            if result['content_hash'] not in seen_hashes:
                processed.append(result)
                seen_hashes.add(result['content_hash'])
            else:
                logger.debug(f"Duplicate content skipped: {result['title']}")
                
        except Exception as e:
            logger.error(f"Failed to process item: {e}")
            continue
    
    return processed