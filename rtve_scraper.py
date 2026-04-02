"""
RTVE Scraper Module - Usando urllib de Python
Handles scraping of RTVE live channels and on-demand content
"""

import json
import logging
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RTVEScraperCache:
    """Simple cache with TTL support"""
    
    def __init__(self, ttl_seconds=1800):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.debug("Cache hit for " + key)
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())
        logger.debug("Cache set for " + key)
    
    def clear(self):
        self.cache.clear()
        logger.info("Cache cleared")


class RTVEScraper:
    """RTVE Content Scraper"""
    
    def __init__(self, timeout=10, max_retries=3, cache_ttl=1800, enable_cache=True):
        self.base_url = 'https://www.rtve.es'
        self.api_url = 'https://www.rtve.es/api'
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self.cache = RTVEScraperCache(cache_ttl)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def set_custom_user_agent(self, user_agent):
        if user_agent:
            self.headers['User-Agent'] = user_agent
            logger.info("Custom User-Agent set")
    
    def _fetch_json(self, url):
        try:
            logger.debug("Fetching: " + url)
            
            req = urllib.request.Request(url, headers=self.headers)
            
            for attempt in range(self.max_retries):
                try:
                    response = urllib.request.urlopen(req, timeout=self.timeout)
                    data = response.read().decode('utf-8')
                    response.close()
                    return json.loads(data)
                except urllib.error.URLError as e:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning("Retrying in " + str(wait_time) + " seconds...")
                        time.sleep(wait_time)
                    else:
                        raise
            
            return {}
        
        except urllib.error.HTTPError as e:
            logger.error("HTTP error " + str(e.code) + " fetching " + url)
            return {}
        except urllib.error.URLError as e:
            logger.error("Connection error fetching " + url)
            return {}
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from " + url)
            return {}
        except Exception as e:
            logger.error("Error fetching " + url + ": " + str(e))
            return {}
    
    def get_live_channels(self):
        cache_key = 'live_channels'
        
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = self.api_url + '/livestreams/live.json'
            data = self._fetch_json(url)
            
            channels = []
            if data and 'page' in data and 'items' in data['page']:
                for item in data['page']['items']:
                    channel = {
                        'id': item.get('id'),
                        'title': item.get('name', 'Unknown'),
                        'url': item.get('url_video'),
                        'icon': item.get('image_url'),
                        'description': item.get('description', '')
                    }
                    if channel['url'] and channel['id']:
                        channels.append(channel)
            
            logger.info("Found " + str(len(channels)) + " live channels")
            
            if self.enable_cache:
                self.cache.set(cache_key, channels)
            
            return channels
        except Exception as e:
            logger.error("Error in get_live_channels: " + str(e))
            return []
    
    def get_on_demand(self, page=1):
        cache_key = 'on_demand_page_' + str(page)
        
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = self.api_url + '/programas/?page=' + str(page)
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
            
            logger.info("Found " + str(len(programs)) + " programs")
            
            if self.enable_cache:
                self.cache.set(cache_key, programs)
            
            return programs
        except Exception as e:
            logger.error("Error in get_on_demand: " + str(e))
            return []
    
    def get_video_url(self, video_id):
        cache_key = 'video_url_' + str(video_id)
        
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = self.api_url + '/videos/' + str(video_id) + '.json'
            data = self._fetch_json(url)
            
            if data and 'video' in data and 'url_video' in data['video']:
                video_url = data['video']['url_video']
                
                if self._is_valid_url(video_url):
                    logger.info("Retrieved video URL for " + str(video_id))
                    
                    if self.enable_cache:
                        self.cache.set(cache_key, video_url)
                    
                    return video_url
            
            logger.warning("No video URL found for " + str(video_id))
            return None
        except Exception as e:
            logger.error("Error getting video URL: " + str(e))
            return None
    
    def get_programs(self):
        cache_key = 'programs_list'
        
        if self.enable_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
        
        try:
            url = self.api_url + '/programas.json'
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
            
            logger.info("Found " + str(len(programs)) + " programs")
            
            if self.enable_cache:
                self.cache.set(cache_key, programs)
            
            return programs
        except Exception as e:
            logger.error("Error in get_programs: " + str(e))
            return []
    
    def _is_valid_url(self, url):
        try:
            result = urlparse(url)
            return bool(result.scheme and result.netloc)
        except:
            return False
    
    def clear_cache(self):
        self.cache.clear()
    
    def get_cache_stats(self):
        return {
            'cached_items': len(self.cache.cache),
            'cache_ttl': self.cache.ttl
        }
