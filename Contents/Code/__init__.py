# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

####################################################################################################

VIDEO_PREFIX = "/video/sbs"
NAME = L('Title')

DEFAULT_CACHE_INTERVAL = 1800
OTHER_CACHE_INTERVAL = 300

ART           = 'art-default.png'
ICON          = 'icon-default.png'

TOP_LEVEL = { "naca": "News & Current Affairs",
              "twg": "The World Game",
              "film": "SBS Film",
              "food": "SBS Food",
              "programs": "Full Episodes" }

BASE_URL = "http://player.sbs.com.au"
SETTINGS_URL = BASE_URL + "/playerassets/%s/standalone_settings.xml"



####################################################################################################

def Start():
    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, L('VideoTitle'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)

    HTTP.SetCacheTime(DEFAULT_CACHE_INTERVAL)

####################################################################################################

def GetMenus(id):
    settingsUrl = SETTINGS_URL % id
    settingsXml = XML.ElementFromURL(settingsUrl)
    
    menuUrl = BASE_URL + settingsXml.xpath('/settings/setting[@name="menuURL"]')[0].get("value")
    menuXml = XML.ElementFromURL(menuUrl, cacheTime=OTHER_CACHE_INTERVAL)
    
    path = [BASE_URL, id + "#", menuXml.get("name")]
    
    menus = []
    for topMenuXml in menuXml.xpath("/menu/menu"):
        path.append(topMenuXml.get("name"))
        
        menu = {}
        menus.append(menu)
        menu['title'] = topMenuXml.find("title").text
        menu['submenus'] = []
        for subMenuXml in topMenuXml.xpath("menu"):
            path.append(subMenuXml.get("name"))
            
            subMenu = {}
            subMenu['title'] = subMenuXml.find("title").text
            subMenu['path'] = '/'.join(path)
            subMenu['playlist'] = BASE_URL + subMenuXml.find("playlist").get("xmlSrc")
            try:
                subMenu['ad'] = subMenuXml.xpath('media/video[@type="doubleClickPreroll"]')[0].get("src")
            except:
                subMenu['ad'] = None
            menu['submenus'].append(subMenu)
            
            path.pop()
            
        path.pop()
            
    return menus

def GetPlaylist(playlistUrl, currentPath):
    playlistXml = XML.ElementFromURL(playlistUrl, cacheTime=OTHER_CACHE_INTERVAL)
    playlist = []
    for videoXml in playlistXml.xpath("/playlist/video"):
        video = {}
        video['title'] = videoXml.find("title").text
        video['summary'] = videoXml.find("description").text
        video['duration'] = int(videoXml.find("duration").text)
        video['thumb'] = videoXml.xpath("media/image")[0].get("src")
        video['url'] = currentPath + "/playlist/" + videoXml.get("name") + "/"
#        video['url'] = GetVideoUrl(BASE_URL + videoXml.get("src"))
#        if video['url']:
        playlist.append(video)

    return playlist

def GetVideoUrl(smilUrl):
    smilXml = XML.ElementFromURL(smilUrl)
    base = smilXml.xpath("/smil/head/meta")[0].get("base")
    
    videos = [(float(v.get("system-bitrate", "0")), v.get("src")) for v in smilXml.xpath("/smil/body/switch/video")]
    videos.sort(reverse=True)
    
    if len(videos) == 0:
        return None
    
    video = videos[0][1]
   
    if base[:4] == "rtmp" and video[-4:] == ".flv":
        video = video[:-4]
        
    return (base, video)

####################################################################################################

def VideoMainMenu():
    dir = MediaContainer(viewGroup="InfoList")

    sortedTopLevel = [(v, k) for (k, v) in TOP_LEVEL.iteritems()]
    sortedTopLevel.sort()
    for name, id in sortedTopLevel:
        dir.Append(Function(DirectoryItem(TopLevelMenu, name), id=id))

    return dir

def TopLevelMenu(sender, id):
    dir = MediaContainer(viewGroup="InfoList", title2=sender.itemTitle)
    
    for menu in GetMenus(id):
        dir.Append(Function(DirectoryItem(MidLevelMenu, menu['title']), menu=menu, title1=dir.title2))
    
    return dir

def MidLevelMenu(sender, menu, title1):
    dir = MediaContainer(viewGroup="InfoList", title1=title1, title2=sender.itemTitle)

    for subMenu in menu['submenus']:
        dir.Append(Function(DirectoryItem(SubLevelMenu, subMenu['title']), subMenu=subMenu, title1=dir.title2))
        
    return dir
    
def SubLevelMenu(sender, subMenu, title1):
    dir = MediaContainer(viewGroup="InfoList", title1=title1, title2=sender.itemTitle)
    
    for video in GetPlaylist(subMenu['playlist'], subMenu['path']):
        dir.Append(WebVideoItem(video['url'], title=video['title'], summary=video['summary'], duration=video['duration'], thumb=video['thumb']))

#        if video['url'][0][:4] == "rtmp":
#            dir.Append(RTMPVideoItem(url=video['url'][0], clip=video['url'][1], width=530, height=298, title=video['title'], summary=video['summary'], 
#                                     duration=video['duration'], thumb=video['thumb']))
#        else:
#            url = video['url'][0] + video['url'][1]
#            dir.Append(VideoItem(url, title=video['title'], summary=video['summary'], 
#                                     duration=video['duration'], thumb=video['thumb']))

    return dir

    

