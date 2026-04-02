
"""
RTVE Scraper Module
Handles scraping of RTVE live channels and on-demand content
"""

import requests
import json
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class RTVEScraper:
    def __init__(self):
        self.base_url = 'https://www.rtve.es'
        self.api_url = 'https://www.rtve.es/api'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_live_channels(self):
        """Fetch live TV channels"""
        try:
            url = f'{self.api_url}/livestreams/live.json'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            channels = []
            if 'page' in data and 'items' in data['page']:
                for item in data['page']['items']:
                    channel = {
                        'id': item.get('id'),
                        'title': item.get('name', 'Unknown'),
                        'url': item.get('url_video'),
                        'icon': item.get('image_url'),
                        'description': item.get('description', '')
                    }
                    if channel['url']:
                        channels.append(channel)
            
            logger.info(f"Found {len(channels)} live channels")
            return channels
        
        except requests.RequestException as e:
            logger.error(f"Error fetching live channels: {e}")
            return []
    
    def get_on_demand(self):
        """Fetch on-demand content"""
        try:
            url = f'{self.api_url}/programas/'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            programs = []
            if 'page' in data and 'items' in data['page']:
                for item in data['page']['items']:
                    program = {
                        'id': item.get('id'),
                        'title': item.get('name', 'Unknown'),
                        'description': item.get('description', ''),
                        'icon': item.get('image_url'),
                        'url': item.get('url')
                    }
                    programs.append(program)
            
            logger.info(f"Found {len(programs)} programs")
            return programs
        
        except requests.RequestException as e:
            logger.error(f"Error fetching on-demand content: {e}")
            return []
    
    def get_video_url(self, video_id):
        """Get direct video URL for playback"""
        try:
            url = f'{self.api_url}/videos/{video_id}.json'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'video' in data and 'url_video' in data['video']:
                return data['video']['url_video']
            
            return None
        
        except requests.RequestException as e:
            logger.error(f"Error fetching video URL: {e}")
            return None
