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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

addon = xbmcaddon.Addon()
handle = int(sys.argv[1])
base_url = sys.argv[0]

# Safe settings parsing
def get_int_setting(setting_name, default_value):
    try:
        value = addon.getSetting(setting_name)
        if value and value.strip():
            return int(value)
        return default_value
    except (ValueError, TypeError):
        return default_value

def get_bool_setting(setting_name, default_value=False):
    try:
        value = addon.getSetting(setting_name)
        return value == 'true'
    except:
        return default_value

def get_string_setting(setting_name, default_value=''):
    try:
        value = addon.getSetting(setting_name)
        if value:
            return value
        return default_value
    except:
        return default_value

# Get settings with safe defaults
timeout = get_int_setting('connection_timeout', 10)
max_retries = get_int_setting('max_retries', 3)
enable_cache = get_bool_setting('enable_cache', True)
custom_ua = get_string_setting('user_agent', '')

# Initialize scraper
scraper = RTVEScraper(
    timeout=timeout,
    max_retries=max_retries,
    enable_cache=enable_cache
)

if custom_ua:
    scraper.set_custom_user_agent(custom_ua)


def build_url(query):
    return base_url + '?' + urlencode(query)


def add_directory_item(label, url, is_folder=True, icon='', description=''):
    li = xbmcgui.ListItem(label=label)
    if icon:
        li.setArt({'icon': icon, 'thumb': icon})
    if description:
        li.setInfo('video', {'plot': description})
    xbmcplugin.addDirectoryItem(handle, url, li, isFolder=is_folder)


def list_categories():
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
    logger.info("Playing video: " + title)
    
    if not url:
        xbmcgui.Dialog().notification(
            'RTVE',
            'URL de video invalida',
            xbmcgui.NOTIFICATION_ERROR
        )
        return
    
    try:
        li = xbmcgui.ListItem(path=url)
        li.setInfo('video', {'title': title})
        xbmcplugin.setResolvedUrl(handle, True, li)
    except Exception as e:
        logger.error("Error playing video: " + str(e))
        xbmcgui.Dialog().notification(
            'RTVE',
            'Error al reproducir el video',
            xbmcgui.NOTIFICATION_ERROR
        )


def router(params):
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
        logger.error("Addon error: " + str(e))
        xbmcgui.Dialog().notification(
            'RTVE',
            'Error en el addon',
            xbmcgui.NOTIFICATION_ERROR
        )
