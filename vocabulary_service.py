import requests
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class VocabularyService:
    def __init__(self):
        self.dictionary_api_url = "https://api.dictionaryapi.dev/api/v2/entries/en"
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
        self.pexels_api_url = "https://api.pexels.com/v1/search"

    def get_word_details(self, word: str) -> Optional[Dict]:
        """
        Get comprehensive details for a word including definition, examples, and image
        """
        try:
            # Get definition from Free Dictionary API
            response = requests.get(f"{self.dictionary_api_url}/{word}")
            if response.status_code != 200:
                return None
            
            data = response.json()[0]
            
            # Extract relevant information
            word_data = {
                'word': data['word'],
                'phonetic': data.get('phonetic', ''),
                'meanings': [],
                'examples': [],
                'image_url': None
            }
            
            # Process meanings
            for meaning in data['meanings']:
                word_data['meanings'].append({
                    'part_of_speech': meaning['partOfSpeech'],
                    'definitions': [d['definition'] for d in meaning['definitions']]
                })
            
            # Get example sentences (first definition's example if available)
            for meaning in data['meanings']:
                for definition in meaning['definitions']:
                    if 'example' in definition:
                        word_data['examples'].append(definition['example'])
            
            # Get related image from Pexels
            if self.pexels_api_key:
                image_response = requests.get(
                    self.pexels_api_url,
                    headers={'Authorization': self.pexels_api_key},
                    params={'query': word, 'per_page': 1}
                )
                if image_response.status_code == 200:
                    photos = image_response.json().get('photos', [])
                    if photos:
                        word_data['image_url'] = photos[0]['src']['medium']
            
            return word_data
            
        except Exception as e:
            print(f"Error fetching word details: {str(e)}")
            return None

    def get_category_words(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Get a list of words for a specific category
        """
        # This is a simplified version. In a real application, you would:
        # 1. Have a predefined list of words for each category
        # 2. Or use a more sophisticated API to get category-specific words
        sample_words = {
            'greetings': ['hello', 'goodbye', 'welcome', 'farewell', 'hi'],
            'business': ['meeting', 'presentation', 'deadline', 'budget', 'project'],
            'food': ['restaurant', 'menu', 'appetizer', 'entree', 'dessert'],
            'travel': ['passport', 'itinerary', 'reservation', 'destination', 'luggage'],
            'slang': ['cool', 'awesome', 'dude', 'chill', 'lit'],
            'phrases': ['how are you', 'nice to meet you', 'what time is it', 'excuse me', 'thank you'],
            'emergency': ['help', 'emergency', 'hospital', 'police', 'fire'],
            'idioms': ['break a leg', 'piece of cake', 'raining cats and dogs', 'hit the hay', 'under the weather']
        }
        
        words = sample_words.get(category.lower(), [])[:limit]
        return [self.get_word_details(word) for word in words if word] 