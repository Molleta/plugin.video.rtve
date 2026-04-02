import sys
import xbmcplugin
import xbmcgui
import xbmcaddon
from urllib.parse import parse_qs, urlencode

# Get addon instance
addon = xbmcaddon.Addon()
handle = int(sys.argv[1])
base_url = sys.argv[0]

def get_categories():
    """Return list of main categories"""
    return [
        {
            'name': 'En directo',
            'icon': 'DefaultFolder.png',
            'url': base_url + '?' + urlencode({'action': 'list_live'})
        },
        {
            'name': 'A la carta',
            'icon': 'DefaultFolder.png',
            'url': base_url + '?' + urlencode({'action': 'list_vod'})
        },
        {
            'name': 'Programas',
            'icon': 'DefaultFolder.png',
            'url': base_url + '?' + urlencode({'action': 'list_programs'})
        }
    ]

def list_categories():
    """List main categories"""
    categories = get_categories()
    for cat in categories:
        li = xbmcgui.ListItem(label=cat['name'])
        li.setArt({'icon': cat['icon']})
        xbmcplugin.addDirectoryItem(handle, cat['url'], li, isFolder=True)
    xbmcplugin.endOfDirectory(handle)

def list_live():
    """List live channels"""
    channels = [
        {'title': 'La 1', 'url': 'http://example.com/la1'},
        {'title': 'La 2', 'url': 'http://example.com/la2'},
        {'title': '3/24', 'url': 'http://example.com/3-24'},
    ]
    for channel in channels:
        li = xbmcgui.ListItem(label=channel['title'])
        url = base_url + '?' + urlencode({'action': 'play', 'url': channel['url']})
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)
    xbmcplugin.endOfDirectory(handle)

def list_vod():
    """List on-demand content"""
    programs = [
        {'title': 'Programa 1', 'url': 'http://example.com/prog1'},
        {'title': 'Programa 2', 'url': 'http://example.com/prog2'},
    ]
    for program in programs:
        li = xbmcgui.ListItem(label=program['title'])
        url = base_url + '?' + urlencode({'action': 'play', 'url': program['url']})
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)
    xbmcplugin.endOfDirectory(handle)

def play_video(url):
    """Play video"""
    li = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(handle, True, li)

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
        elif action == 'play':
            url = params.get('url', [''])[0]
            play_video(url)
        else:
            list_categories()

if __name__ == '__main__':
    params = parse_qs(sys.argv[2].lstrip('?'))
    router(params)
