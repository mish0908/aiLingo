import requests
from typing import Dict, List, Optional, Union
import os
from dotenv import load_dotenv
import json
import random
from pydantic import BaseModel, Field
from openai import OpenAI

load_dotenv()

class WordMeaning(BaseModel):
    part_of_speech: str
    definitions: List[str]

class WordDetails(BaseModel):
    word: str
    phonetic: str
    chinese: str
    pinyin: str
    meanings: List[WordMeaning]
    examples: List[str]
    chinese_examples: List[str]
    usage_notes: str
    is_slang: bool

class CategoryWords(BaseModel):
    words: List[str]

class VocabularyService:
    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.client = OpenAI(api_key=self.openrouter_api_key, base_url="https://openrouter.ai/api/v1")
        self.model = "openai/gpt-4.1"
        load_dotenv()
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'word_cache.json')
        self.word_cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """
        Load the word cache from the JSON file if it exists
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache file: {str(e)}")
                return {}
        return {}
        
    def _save_to_cache(self, word: str, details: Dict) -> None:
        """
        Save word details to the cache file
        """
        try:
            self.word_cache[word] = details
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.word_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")

    def get_word_details(self, word: str) -> Optional[Dict]:
        """
        Get comprehensive details for a word including definition and example translations.
        First checks the cache, and if not found, fetches from the API and caches the result.
        """
        # Normalize the word to lowercase for consistent caching
        word_normalized = word.lower().strip()
        
        # Check if the word is in the cache
        if word_normalized in self.word_cache:
            print(f"Cache hit for word: {word_normalized}")
            return self.word_cache[word_normalized]
            
        print(f"Cache miss for word: {word_normalized}, fetching from API")
        
        try:
            # Get definition and translations using OpenAI structured output
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a language learning assistant that provides detailed information about English words including definitions, examples, Chinese translations, and usage notes."},
                    {"role": "user", "content": f"Provide comprehensive details for the English word '{word}'. Include phonetics, meanings, example sentences, Chinese translations, and usage notes."}
                ],
                response_format=WordDetails
            )

            word_data = completion.choices[0].message.parsed
            
            # Convert to dictionary format for compatibility with existing code
            result = {
                'word': word_data.word,
                'phonetic': word_data.phonetic,
                'chinese': word_data.chinese,
                'pinyin': word_data.pinyin,
                'meanings': [{'part_of_speech': m.part_of_speech, 'definitions': m.definitions} for m in word_data.meanings],
                'examples': word_data.examples,
                'chinese_examples': word_data.chinese_examples,
                'usage_notes': word_data.usage_notes,
                'is_slang': word_data.is_slang
            }
            
            # Save the result to cache
            self._save_to_cache(word_normalized, result)
            
            return result
            
        except Exception as e:
            print(f"Error fetching word details: {str(e)}")
            return None

    def _is_likely_slang_text(self, text: str) -> bool:
        """
        Determine if text likely contains slang based on common slang terms
        """
        # List of common American slang terms
        common_slang = [
            'cool', 'lit', 'dope', 'sick', 'woke', 'salty', 'extra', 'basic', 
            'ghosting', 'flex', 'savage', 'fam', 'vibe', 'sus', 'cap', 'yeet',
            'slay', 'stan', 'bae', 'goat', 'lowkey', 'highkey', 'fire', 'bet',
            'chill', 'legit', 'sketchy', 'thirsty', 'throw shade', 'wasted',
            'hyped', 'on point', 'clutch', 'bougie', 'ride or die', 'squad',
            'tight', 'turnt', 'ratchet', 'shook', 'simp', 'karen', 'snatched',
            'spill the tea', 'clout', 'ghost', 'flex', 'salty', 'extra'
        ]
        
        # Check if any word in the text is a common slang term
        words = text.lower().split()
        for word in words:
            # Remove punctuation for comparison
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word in common_slang:
                return True
                
        # Check for common slang phrases
        text_lower = text.lower()
        slang_phrases = [
            'throw shade', 'spill the tea', 'ride or die', 'on point',
            'low key', 'high key', 'turn up', 'hit different'
        ]
        
        for phrase in slang_phrases:
            if phrase in text_lower:
                return True
                
        return False

    def get_category_words(self, category: str, limit: int = 5) -> List[Dict]:
        """
        Get a list of words for a specific category using OpenAI structured output
        """
        try:
            # Get words for the category using OpenAI
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a language learning assistant that provides relevant vocabulary words for specific categories."},
                    {"role": "user", "content": f"Generate a list of {limit} English words related to the category '{category}'. These should be useful for language learners."}
                ],
                response_format=CategoryWords
            )
            
            category_words = completion.choices[0].message.parsed.words
            
            # Process each word to get complete details
            processed_words = []
            for word in category_words:
                if word:
                    word_details = self.get_word_details(word)
                    if word_details:
                        processed_words.append(word_details)
                    
            return processed_words
        except Exception as e:
            print(f"Error getting category words: {str(e)}")
            return self._get_predefined_words(category, limit)

    def _get_predefined_words(self, category: str, limit: int = 5) -> List[Dict]:
        """
        Get fallback words for a category using a simpler AI prompt when the main method fails
        """
        try:
            # Use a simpler prompt as fallback
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful language learning assistant."},
                    {"role": "user", "content": f"List exactly {limit} common English words related to '{category}', one word per line. Only provide the words, nothing else."}
                ]
            )
            
            # Parse the response to get words
            response_text = completion.choices[0].message.content.strip()
            words = [word.strip() for word in response_text.split('\n') if word.strip()]
            
            # Limit to the requested number
            words = words[:limit]
            
            # Get details for each word
            processed_words = []
            for word in words:
                word_details = self.get_word_details(word)
                if word_details:
                    processed_words.append(word_details)
                    
            return processed_words
        except Exception as e:
            print(f"Error in fallback word generation: {str(e)}")
            # Return minimal data as a last resort
            return [{"word": category, "meanings": [{"part_of_speech": "noun", "definitions": [f"A term related to {category}"]}]}]

    def get_random_words(self, category: str = None, limit: int = 10) -> List[Dict]:
        """
        Get random words from a specific category or all categories
        """
        if category:
            words = self.get_category_words(category, limit=limit)
        else:
            # Use OpenAI to generate random words across categories
            try:
                completion = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a language learning assistant that provides diverse vocabulary words across different categories."},
                        {"role": "user", "content": f"Generate a list of {limit} diverse English words useful for language learners. Include a mix of common words, phrases, and expressions from different categories."}
                    ],
                    response_format=CategoryWords
                )
                
                random_words = completion.choices[0].message.parsed.words
                
                # Process each word to get complete details
                words = []
                for word in random_words:
                    if word:
                        word_details = self.get_word_details(word)
                        if word_details:
                            words.append(word_details)
            except Exception as e:
                print(f"Error getting random words: {str(e)}")
                # Fallback to original implementation
                words = []
                for cat in ['greetings', 'business', 'food', 'travel', 'slang', 'phrases', 'emergency', 'idioms']:
                    words.extend(self.get_category_words(cat, limit=2))
        
        # Filter out None values and get unique words
        words = [word for word in words if word is not None]
        unique_words = list({w['word']: w for w in words}.values())
        
        # Shuffle and return requested number of words
        random.shuffle(unique_words)
        return unique_words[:limit]

    def generate_study_session(self, category: str = None, word_count: int = 5) -> List[Dict]:
        """
        Generate a study session with random words from a category or all categories
        """
        words = self.get_random_words(category, word_count)
        return words