import re

####################################################################################################

TWIT_VIDEO_PREFIX        = "/video/twittv"
TWIT_MUSIC_PREFIX        = "/music/twittv"

TWIT_FRONTPAGE           = "http://twit.tv" # Do not append a trailing slash
TWIT_LISTPAGE            = "http://twit.tv/shows"
TWIT_LIVE                = "http://live.twit.tv/"

ITUNES_NAMESPACE         = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}

DATE_FORMAT              = '%a, %d %b %Y'

CACHE_INTERVAL           = 3600
CACHE_LISTPAGE_INTERVAL  = 172800
CACHE_SHOWPAGE_INTERVAL  = 172800
CACHE_RSS_FEED_INTERVAL  = 3600

ICON = "icon-default.png"
ART = "art-default.jpg"

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(TWIT_VIDEO_PREFIX, MainMenu, "TWiT.TV", ICON, ART)
  Plugin.AddPrefixHandler(TWIT_MUSIC_PREFIX, MainMenu, "TWiT.TV", ICON, ART)

  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  MediaContainer.content = "Items"
  MediaContainer.title1 = "TWiT.TV"
  MediaContainer.art = R(ART)
  MediaContainer.viewGroup = "InfoList"
  DirectoryItem.thumb = R(ICON)
  HTTP.CacheTime = CACHE_INTERVAL

####################################################################################################
def UpdateCache():
  HTTP.Request(TWIT_LISTPAGE, cacheTime=CACHE_LISTPAGE_INTERVAL)
  # Request the MainMenu's to cache the show pages
  MainMenu(cacheUpdate=True)

####################################################################################################
def MainMenu(cacheUpdate=False):

  # Top level menu
  # Show available shows

  dir = MediaContainer()

  # Add TWiT Live entry
  dir.Append(WebVideoItem(TWIT_LIVE, title='TWiT Live', summary="In May, 2008 Leo Laporte started broadcasting live video from the TWiT Brick House in Petaluma, CA. This video allows viewers to watch the creation process of all of the TWiT netcasts and enables them to interact with Leo through one of the associated chats.", thumb=R('icon-twitlive.png')))

  resultDict = {}

  @parallelize
  def GetShows():
    page = HTML.ElementFromURL(TWIT_LISTPAGE + '/', cacheTime=CACHE_LISTPAGE_INTERVAL)
    shows = page.xpath("//li/span[@class='views-field views-field-title']//a")

    for num in range(len(shows)):
      show = shows[num]

      @task
      def GetShow(num=num, resultDict=resultDict, show=show):
        showName = str(show.xpath("./text()")[0]);

        # Add TWIT_FRONTPAGE to the beginning of the link if it's not there
        showUrl = show.xpath(".")[0].get('href')
        if showUrl.count(TWIT_FRONTPAGE) == 0:
          showUrl = TWIT_FRONTPAGE + showUrl

        # Pull the show page down
        showPage = HTML.ElementFromURL(showUrl, cacheTime=CACHE_SHOWPAGE_INTERVAL)
    
        # Make sure the page has feeds
        if showPage.xpath("//div[@class='sources-dropdown']//option[text() and @value!=0]"):
          # Get the show image
          showImage = showPage.xpath("//div[@class='views-field views-field-field-cover-art-fid']/span/img")
          if showImage:
            showImage = showImage[0].get('src')
          else:
            showImage = None

          resultDict[num] = DirectoryItem(key=Function(ShowBrowser, showName=showName, showUrl=showUrl), title=showName, summary=showName, thumb=Function(GetThumb, url=showImage))

  keys = resultDict.keys()
  keys.sort()
  for key in keys:
    dir.Append(resultDict[key])

  return dir

####################################################################################################
def ShowBrowser(sender, showName, showUrl):

  dir = MediaContainer(title2=showName)

  # Find link to best quality RSS feed from show page.

  showPage = HTML.ElementFromURL(showUrl, cacheTime=CACHE_SHOWPAGE_INTERVAL)

  feedOptions = showPage.xpath("//div[@class='sources-dropdown']//option[text()]");
  feedUrl = ''

  for feedOption in feedOptions:

    feedOptionName = str(feedOption.xpath("./text()")[0])
    feedOptionUrl= feedOption.get('value')

    # Match feeds with "RSS" in the name
    if 'RSS' in feedOptionName:
      feedUrl = feedOptionUrl

      # The first match with "video" in the URL (if any) should be higher quality
      if 'video' in feedOptionUrl:
        break

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
      item = TrackItem(episodeUrl, title=episodeTitle, artist=showName, album=showName, summary=episodeDescription, subtitle=episodeSubtitle, duration=episodeLength, thumb=Function(GetThumb, url=episodeImage))
    else:
      item = VideoItem(episodeUrl, title=episodeTitle, subtitle=episodeSubtitle, summary=episodeDescription, duration=episodeLength, thumb=Function(GetThumb, url=episodeImage))

    dir.Append(item)

  return dir

####################################################################################################
def GetThumb(url):
  if url:
    try:
      data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
      return DataObject(data, 'image/jpeg')
    except:
      pass

  return Redirect(R(ICON))
