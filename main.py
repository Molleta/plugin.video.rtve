"""
RTVE Kodi Addon - Main Plugin
Provides interface for RTVE live channels and on-demand content
"""

import sys
import xbmcplugin
import xbmcgui
import xbmcaddon
import logging
from urllib.parse import parse_qs, urlencode

from rtve_scraper import RTVEScraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get addon instance
addon = xbmcaddon.Addon()
handle = int(sys.argv[1])
base_url = sys.argv[0]

# Initialize scraper with addon settings
scraper = RTVEScraper(
    timeout=int(addon.getSetting('connection_timeout')) or 10,
    max_retries=int(addon.getSetting('max_retries')) or 3,
    enable_cache=addon.getSetting('enable_cache') == 'true'
)

# Set custom user agent if configured
custom_ua = addon.getSetting('user_agent')
if custom_ua:
    scraper.set_custom_user_agent(custom_ua)

def build_url(query):
    """Build URL with query parameters"""
    return base_url + '?' + urlencode(query)

def add_directory_item(label, url, is_folder=True, icon='', description=''):
    """Add directory item to list"""
    li = xbmcgui.ListItem(label=label)
    if icon:
        li.setArt({'icon': icon, 'thumb': icon})
    if description:
        li.setInfo('video', {'plot': description})
    xbmcplugin.addDirectoryItem(handle, url, li, isFolder=is_folder)

def list_categories():
    """List main categories"""
    logger.info("Listing main categories")
    
    categories = [
        {
            'name': 'En directo',
            'action': 'list_live',
            'description': 'Ver canales en vivo'
        },
        {
            'name': 'A la carta',
            'action': 'list_vod',
            'description': 'Ver contenido bajo demanda'
        },
        {
            'name': 'Programas',
            'action': 'list_programs',
            'description': 'Ver lista de programas'
        }
    ]
    
    for cat in categories:
        url = build_url({'action': cat['action']})
        add_directory_item(
            cat['name'],
            url,
            is_folder=True,
            description=cat['description']
        )
    
    xbmcplugin.endOfDirectory(handle)

def list_live():
    """List live channels"""
    logger.info("Listing live channels")
    
    channels = scraper.get_live_channels()
    
    if not channels:
        xbmcgui.Dialog().notification(
            'RTVE',
            'No se pudieron cargar los canales en directo',
            xbmcgui.NOTIFICATION_ERROR
        )
    
    for channel in channels:
        url = build_url({
            'action': 'play',
            'url': channel['url'],
            'title': channel['title']
        })
        add_directory_item(
            channel['title'],
            url,
            is_folder=False,
            icon=channel.get('icon', ''),
            description=channel.get('description', '')
        )
    
    xbmcplugin.endOfDirectory(handle)

def list_vod():
    """List on-demand content"""
    logger.info("Listing on-demand content")
    
    programs = scraper.get_on_demand(page=1)
    
    if not programs:
        xbmcgui.Dialog().notification(
            'RTVE',
            'No se pudo cargar el contenido bajo demanda',
            xbmcgui.NOTIFICATION_ERROR
        )
    
    for program in programs:
        url = build_url({
            'action': 'play',
            'url': program['url'],
            'title': program['title']
        })
        add_directory_item(
            program['title'],
            url,
            is_folder=False,
            icon=program.get('icon', ''),
            description=program.get('description', '')
        )
    
    xbmcplugin.endOfDirectory(handle)

def list_programs():
    """List programs"""
    logger.info("Listing programs")
    
    programs = scraper.get_programs()
    
    if not programs:
        xbmcgui.Dialog().notification(
            'RTVE',
            'No se pudieron cargar los programas',
            xbmcgui.NOTIFICATION_ERROR
        )
    
    for program in programs:
        url = build_url({
            'action': 'play',
            'url': program['url'],
            'title': program['title']
        })
        add_directory_item(
            program['title'],
            url,
            is_folder=False,
            icon=program.get('icon', ''),
            description=program.get('description', '')
        )
    
    xbmcplugin.endOfDirectory(handle)

def play_video(url, title=''):
    """Play video"""
    logger.info(f"Playing video: {title} - {url}")
    
    if not url:
        xbmcgui.Dialog().notification(
            'RTVE',
            'URL de vídeo inválida',
            xbmcgui.NOTIFICATION_ERROR
        )
        return
    
    try:
        li = xbmcgui.ListItem(path=url)
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setInfo('video', {'title': title})
        xbmcplugin.setResolvedUrl(handle, True, li)
    except Exception as e:
        logger.error(f"Error playing video: {e}")
        xbmcgui.Dialog().notification(
            'RTVE',
            'Error al reproducir el vídeo',
            xbmcgui.NOTIFICATION_ERROR
        )

def router(params):
    """Route actions"""
    if not params:
        list_categories()
    else:
        action = params.get('action', [''])[0]
        
        if action == 'list_live':
            list_live()
        elif action == 'list_vod':
            list_vod()
        elif action == 'list_programs':
            list_programs()
        elif action == 'play':
            url = params.get('url', [''])[0]
            title = params.get('title', [''])[0]
            play_video(url, title)
        else:
            list_categories()

if __name__ == '__main__':
    try:
        params = parse_qs(sys.argv[2].lstrip('?'))
        router(params)
    except Exception as e:
        logger.error(f"Addon error: {e}", exc_info=True)
        xbmcgui.Dialog().notification(
            'RTVE',
            'Error en el addon',
            xbmcgui.NOTIFICATION_ERROR
        )
