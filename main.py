# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcgui

__addon__ = xbmcaddon.Addon()

# Basic structure for a Kodi addon

def list_videos():
    videos = [
        {'title': 'Video 1', 'url': 'http://example.com/video1'},
        {'title': 'Video 2', 'url': 'http://example.com/video2'},
    ]
    return videos


def play_video(url):
    xbmc.Player().play(url)

if __name__ == '__main__':
    # Example usage of the functions
    videos = list_videos()
    for video in videos:
        print(video['title'])  # This would be displayed in the Kodi interface.
        # Uncomment the line below to play video
        # play_video(video['url'])