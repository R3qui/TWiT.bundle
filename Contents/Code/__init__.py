import re, string, urllib

####################################################################################################

TWIT_VIDEO_PREFIX                    = "/video/twittv"
TWIT_MUSIC_PREFIX                    = "/music/twittv"

TWIT_FRONTPAGE                       = "http://twit.tv" # Do not append a trailing slash
TWIT_LIVE                            = "http://live.twit.tv/"

ODTV_FRONTPAGE                       = "http://odtv.me/"
ODTV_CATEGORY_REDIRECT               = "http://odtv.me/?cat="
ODTV_RSS_FEED                        = "http://odtv.me/?feed=rss2&category_name="

ITUNES_NAMESPACE                     = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}

DATE_FORMAT                          = '%a, %d %b %Y'

DEBUG_XML_RESPONSE		     = False
CACHE_INTERVAL                       = 3600
CACHE_FRONTPAGE_INTERVAL             = 172800
CACHE_SHOWPAGE_INTERVAL              = 172800
CACHE_RSS_FEED_INTERVAL              = 3600

####################################################################################################

def Start():
  Plugin.AddPrefixHandler(TWIT_VIDEO_PREFIX, MainMenu, L("twit"), "icon-default.png", "art-default.png")
  Plugin.AddPrefixHandler(TWIT_MUSIC_PREFIX, MainMenu, L("twit"), "icon-default.png", "art-default.png")

  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.content = 'Items'
  MediaContainer.title1 = L("twit")
  MediaContainer.art = R('art-default.png')
  HTTP.SetCacheTime(CACHE_INTERVAL)

def UpdateCache():
  HTTP.Request(TWIT_FRONTPAGE, cacheTime=CACHE_FRONTPAGE_INTERVAL)
  HTTP.Request(ODTV_FRONTPAGE, cacheTime=CACHE_FRONTPAGE_INTERVAL)
  # Request the MainMenu's to cache the show pages
  MainMenu(cacheUpdate=True)
  MainMenuOdtv(False, cacheUpdate=True)

def MainMenu(cacheUpdate=False):

  # Top level menu
  # Show available shows

  dir = MediaContainer()
  dir.art = R('art-default.png')

  # Add TWiT Live entry

  dir.Append(WebVideoItem(TWIT_LIVE, 'TWiT Live', summary="In May, 2008 Leo Laporte started broadcasting live video from the TWiT Cottage in Petaluma, CA. This video allows viewers to watch the creation process of all of the TWiT netcasts and enables them to interact with Leo through one of the associated chats. Originally, the video was broadcast on both the ustream.tv and Stickam video services, but is now broadcast entirely over Stickam at live.TWiT.tv", duration='', thumb=R('icon-twitlive.png'), subtitle=''))


  page = HTML.ElementFromURL(TWIT_FRONTPAGE + '/', cacheTime=CACHE_FRONTPAGE_INTERVAL)

  shows = page.xpath("//div[@id='block-menu-menu-our-shows']/div[@class='content']/ul[@class='menu']/li")

  for show in shows:

    showName = str(show.xpath("./a/text()")[0]);

    # Sometimes the link to the page already contains TWIT_FRONTPAGE, sometimes not
    showUrl = show.xpath("./a")[0].get('href')
    if showUrl.count(TWIT_FRONTPAGE) == 0:
      showUrl = TWIT_FRONTPAGE + showUrl

    # Pull the show page down so we can get the shows image
    showPage = HTML.ElementFromURL(showUrl, cacheTime=CACHE_SHOWPAGE_INTERVAL)
    showImage = showPage.xpath("//div[@class='podcast']/img")[0].get('src')

    dir.Append(Function(DirectoryItem(ShowBrowser, title=showName, summary=showName, subtitle='', thumb=showImage), showName=showName, showUrl=showUrl))

  # Append a link for 'odtv' to the 'twit' showlist
  dir.Append(Function(DirectoryItem(MainMenuOdtv, title='oDTV : on-Demand TWiT Video', summary='on-Demand TWiT Video', subtitle='', thumb=R('icon-odtv.png'), art=R('art-odtv.png'))))


  if DEBUG_XML_RESPONSE and not cacheUpdate:
    PMS.Log(dir.Content())
  return dir


def ShowBrowser(sender, showName, showUrl):

  dir = MediaContainer()
  dir.title2 = showName
  dir.viewGroup = 'Details'

  # Find link to best quality RSS feed from show page.

  showPage = HTML.ElementFromURL(showUrl, cacheTime=CACHE_SHOWPAGE_INTERVAL)

  feedOptions = showPage.xpath("//div[@class='podcast']/select/option");
  feedUrl = ''

  for feedOption in feedOptions:

    # We want to match these feed types, fortunately the best quality ones are found last in the list
    # RSS
    # AAC Version: RSS
    # RSS (Desktop version)

    feedOptionName = str(feedOption.xpath("./text()")[0])
    feedOptionUrl= feedOption.get('value')

    if feedOptionName == 'RSS' or feedOptionName == 'AAC Version: RSS' or feedOptionName == 'RSS (Desktop version)':
      feedUrl = feedOptionUrl

  feed = XML.ElementFromURL(feedUrl, cacheTime=CACHE_RSS_FEED_INTERVAL)

  feedMetadata = feed.xpath("//channel")[0]
  feedImage = feedMetadata.xpath("./itunes:image", namespaces=ITUNES_NAMESPACE)[0].get('href')

  episodes = feed.xpath("//channel/item")

  for episode in episodes:

    episodeTitle = episode.xpath("./title/text()")[0]

    # Set the subtitle to the date
    episodeDate = str(episode.xpath("./pubDate/text()")[0])
    episodeDate = Datetime.ParseDate(episodeDate)
    episodeLocalDate = episodeDate
    episodeSubtitle = episodeLocalDate.strftime(DATE_FORMAT)

    # Get the description
    if len (episode.xpath("./itunes:summary/text()", namespaces=ITUNES_NAMESPACE)) > 0:
      episodeDescription = episode.xpath("./itunes:summary/text()", namespaces=ITUNES_NAMESPACE)[0]
    else:
      episodeDescription = episode.xpath("./description/text()")[0]

    # Remove some text from the description which is no use
    episodeDescription = re.sub(r'FriendFeed for TWiT Shows\n?', '', episodeDescription)
    episodeDescription = re.sub(r'Wiki for this episode\n?', '', episodeDescription)
    episodeDescription = re.sub(r'Wiki show notes for this episode\n?', '', episodeDescription)

    # Sometimes new lines are missing from the description
    if not re.search(r'\n', episodeDescription):
      episodeDescription = re.sub(r'\.\s', r'.\n\n', episodeDescription)

    # Add some extra white space for formatting
    episodeDescription = '\n' + episodeDescription

    # Episodes don't have individual images so just use the one for the show
    episodeImage = feedImage

    # Episodes are available in flv or in a higher quality in either mp4 or m4v
    episodeUrl = episode.xpath("./enclosure")[0].get('url')

    # See if we have a length element
    episodeLength = 0
    if len(episode.xpath("./itunes:duration/text()", namespaces=ITUNES_NAMESPACE)) > 0:
      episodeLength = episode.xpath("./itunes:duration/text()", namespaces=ITUNES_NAMESPACE)[0]
      # Formatting is either 'seconds' 'hh:mm:ss' or 'mm:ss'
      if re.search(r':', episodeLength):
        episodeLengthParts = re.search(r'((\d*):)?(\d+):(\d+)', episodeLength)
        if episodeLengthParts.group(2) is not None:
          # Time has hours minutes and seconds
          episodeLengthSeconds = (int(episodeLengthParts.group(2)) * 3600 )+ ( int(episodeLengthParts.group(3)) * 60 ) +  int(episodeLengthParts.group(4))
        else:
          # Time has just minutes and seconds
          episodeLengthSeconds = int(episodeLengthParts.group(3)) * 60  +  int(episodeLengthParts.group(4))
      else:
        episodeLengthSeconds = int(episodeLength)
      episodeLength = str(episodeLengthSeconds * 1000)

    # Find the media type
    fileType = re.search(r'.*[.]([^.]+)$', episodeUrl).group(1)
    mediaType = ''
    if fileType == 'mov' or fileType =='mp4':
      episodeSubtitle += "\nVideo"
      mediaType = 'video'
    else:
      episodeSubtitle += "\nAudio"
      mediaType = 'audio'
    episodeSubtitle += " [ " + fileType + " ] "

    if mediaType == 'audio':
      item = TrackItem(episodeUrl, episodeTitle, artist=showName, album=showName, summary=episodeDescription, subtitle=episodeSubtitle, duration=episodeLength, thumb=episodeImage)
    else:
      item = VideoItem(episodeUrl, episodeTitle, episodeSubtitle, episodeDescription, episodeLength, thumb=episodeImage)

    dir.Append(item)

  if DEBUG_XML_RESPONSE:
    PMS.Log(dir.Content())
  return dir


def MainMenuOdtv(sender, cacheUpdate=False):

  dir = MediaContainer()
  dir.title1 = L('twit')
  dir.title2 = L('odtv')
  dir.art = R('art-odtv.png')

  page = HTML.ElementFromURL(ODTV_FRONTPAGE, cacheTime=CACHE_FRONTPAGE_INTERVAL)

  shows = page.xpath("//select[@name='cat']/option")

  for show in shows:
    # For each show we need to find the shows 'short name'
    showId = show.get('value')
    if int(showId) > 0:
     # showName = TidyString(show.xpath('./text()')[0])
      showName = re.search(r'(.*)\s*\(', show.xpath('./text()')[0]).group(1)
      showName = TidyString(showName)
      # We need the 'short name' for the show, we may already have this in the dictionary
      if Dict.HasKey("shortcode-"+showId):
        showShortCode = Dict.Get("shortcode-"+showId)
      else:
        # We need to pull the referenced page and see where it redirects to to get the 'short name'
        showPage = urllib.urlopen(ODTV_CATEGORY_REDIRECT+showId)
        showShortCode = re.search( r'category/([^/]+)/', str(showPage.geturl())).group(1)
        Dict.Set("shortcode-"+showId, showShortCode)

      dir.Append(Function(DirectoryItem(ShowBrowserOdtv, title=showName, summary=showName, subtitle='', thumb=R('icon-odtv.png')), showName=showName, shortCode=showShortCode))

  if DEBUG_XML_RESPONSE and not cacheUpdate:
    PMS.Log(dir.Content())
  return dir

def ShowBrowserOdtv(sender,showName, shortCode):

  dir = MediaContainer()
  dir.title1 = L('odtv')
  dir.title2 = showName
  dir.viewGroup = 'Details'
  dir.art = R('art-odtv.png')

  feed = XML.ElementFromURL(ODTV_RSS_FEED+shortCode, cacheTime=CACHE_RSS_FEED_INTERVAL)

  episodes = feed.xpath("//item")

  for episode in episodes:

    # Check we have an enclosure
    if len(episode.xpath("./enclosure")) == 0:
      continue
    url = episode.xpath("./enclosure")[0].get('url')
    title = episode.xpath("./title/text()")[0]
    description = episode.xpath("./description/text()")[0]

    episodeDate = str(episode.xpath("./pubDate/text()")[0])
    episodeDate = Datetime.ParseDate(episodeDate)
    episodeLocalDate = episodeDate

    subtitle = episodeLocalDate.strftime(DATE_FORMAT)

    video = VideoItem(url, title, subtitle, description, 0, thumb=R('icon-odtv.png'))
    dir.Append(video)

  if DEBUG_XML_RESPONSE:
    PMS.Log(dir.Content())
  return dir


def TidyString(stringToTidy):
  # Function to tidy up strings works ok with unicode, 'strip' seems to have issues in some cases so we use a regex
  if stringToTidy:
    # Strip new lines
    stringToTidy = re.sub(r'\n', r' ', stringToTidy)
    # Strip leading / trailing spaces
    stringSearch = re.search(r'^\s*(\S.*?\S?)\s*$', stringToTidy)
    if stringSearch == None: 
      return ''
    else:
      return stringSearch.group(1)
  else:
    return ''

