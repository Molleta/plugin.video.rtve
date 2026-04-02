"""
RTVE Scraper Module - Versión Mejorada
Handles scraping of RTVE live channels and on-demand content
with caching, retry logic, and configurable settings
"""

import requests
import json
import logging
import time
from urllib.parse import urljoin, urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class RTVEScraperCache:
    """Simple cache with TTL support"""
    def __init__(self, ttl_seconds=1800):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key):
        """Get item from cache"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.debug(f"Cache hit for {key}")
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        """Set item in cache"""
        self.cache[key] = (value, time.time())
        logger.debug(f"Cache set for {key}")
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        logger.info("Cache cleared")

class RTVEScraper:
    """RTVE Content Scraper"""
    
    def __init__(self, timeout=10, max_retries=3, cache_ttl=1800, enable_cache=True):
        """
        Initialize RTVEScraper
        
        Args:
            timeout (int): Connection timeout in seconds
            max_retries (int): Maximum number of retries on failure
            cache_ttl (int): Cache time-to-live in seconds
            enable_cache (bool): Enable/disable caching
        """
        self.base_url = 'https://www.rtve.es'
        self.api_url = 'https://www.rtve.es/api'
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self.cache = RTVEScraperCache(cache_ttl)
        
        # Setup session with retry strategy
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configure session with retry strategy"""
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def set_custom_user_agent(self, user_agent):
        """Set custom User-Agent"""
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})
            logger.info("Custom User-Agent set")
    
    def _fetch_json(self, url):
        """
        Fetch JSON from URL with error handling
        
        Args:
            url (str): URL to fetch
            
        Returns:
            dict: Parsed JSON response or empty dict on error
        """
        try:
            logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {url} (timeout={self.timeout}s)")
            return {}
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error fetching {url}")
            return {}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} fetching {url}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from {url}")
            return {}
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return {}
    
    def get_live_channels(self):
        """
        Fetch live TV channels
        
        Returns:
            list: List of channel dictionaries
        """
        cache_key = 'live_channels'
        
        # Check cache first
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = f'{self.api_url}/livestreams/live.json'
            data = self._fetch_json(url)
            
            channels = []
            if data and 'page' in data and 'items' in data['page']:
                for item in data['page']['items']:
                    channel = {
                        'id': item.get('id'),
                        'title': item.get('name', 'Unknown'),
                        'url': item.get('url_video'),
                        'icon': item.get('image_url'),
                        'description': item.get('description', ''),
                        'duration': item.get('duration', '0')
                    }
                    if channel['url'] and channel['id']:
                        channels.append(channel)
            
            logger.info(f"Found {len(channels)} live channels")
            
            if self.enable_cache:
                self.cache.set(cache_key, channels)
            
            return channels
        
        except Exception as e:
            logger.error(f"Unexpected error in get_live_channels: {e}")
            return []
    
    def get_on_demand(self, page=1):
        """
        Fetch on-demand content with pagination
        
        Args:
            page (int): Page number (default: 1)
            
        Returns:
            list: List of program dictionaries
        """
        cache_key = f'on_demand_page_{page}'
        
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = f'{self.api_url}/programas/?page={page}'
            data = self._fetch_json(url)
            
            programs = []
            if data and 'page' in data and 'items' in data['page']:
                for item in data['page']['items']:
                    program = {
                        'id': item.get('id'),
                        'title': item.get('name', 'Unknown'),
                        'description': item.get('description', ''),
                        'icon': item.get('image_url'),
                        'url': item.get('url'),
                        'duration': item.get('duration', '0'),
                        'broadcast_date': item.get('broadcast_date', '')
                    }
                    programs.append(program)
            
            logger.info(f"Found {len(programs)} programs on page {page}")
            
            if self.enable_cache:
                self.cache.set(cache_key, programs)
            
            return programs
        
        except Exception as e:
            logger.error(f"Unexpected error in get_on_demand: {e}")
            return []
    
    def get_video_url(self, video_id):
        """
        Get direct video URL for playback
        
        Args:
            video_id (str): Video ID
            
        Returns:
            str: Direct video URL or None on error
        """
        cache_key = f'video_url_{video_id}'
        
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = f'{self.api_url}/videos/{video_id}.json'
            data = self._fetch_json(url)
            
            if data and 'video' in data and 'url_video' in data['video']:
                video_url = data['video']['url_video']
                
                if not self._is_valid_url(video_url):
                    logger.warning(f"Invalid video URL for {video_id}: {video_url}")
                    return None
                
                logger.info(f"Retrieved video URL for {video_id}")
                
                if self.enable_cache:
                    self.cache.set(cache_key, video_url)
                
                return video_url
            
            logger.warning(f"No video URL found for {video_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting video URL for {video_id}: {e}")
            return None
    
    def get_programs(self):
        """Fetch list of programs"""
        cache_key = 'programs_list'
        
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = f'{self.api_url}/programas.json'
            data = self._fetch_json(url)
            
            programs = []
            if data and 'page' in data and 'items' in data['page']:
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
            
            if self.enable_cache:
                self.cache.set(cache_key, programs)
            
            return programs
        
        except Exception as e:
            logger.error(f"Error in get_programs: {e}")
            return []
    
    @staticmethod
    def _is_valid_url(url):
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return {
            'cached_items': len(self.cache.cache),
            'cache_ttl': self.cache.ttl
        }
      .
