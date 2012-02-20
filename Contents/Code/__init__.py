TWIT_LIVE = "http://live.twit.tv/"
SHOWS_XML = "http://static.twit.tv/rssFeeds.plist"
ITUNES_NAMESPACE = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
COVER_URL = 'http://leoville.tv/podcasts/coverart/%s600%s.jpg'

DATE_FORMAT = "%a, %d %b %Y"
ICON = "icon-default.png"
ART = "art-default.jpg"

####################################################################################################
def Start():

	Plugin.AddPrefixHandler("/video/twittv", MainMenuVideo, "TWiT.TV", ICON, ART)
	Plugin.AddPrefixHandler("/music/twittv", MainMenuAudio, "TWiT.TV", ICON, ART)

	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")

	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = "TWiT.TV"
	ObjectContainer.view_group = "InfoList"
	DirectoryItem.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def MainMenuVideo():

	oc = ObjectContainer()

	# Add TWiT Live entry
	oc.add(VideoClipObject(key=WebVideoURL(TWIT_LIVE), rating_key=TWIT_LIVE, title="TWiT Live", summary="In May, 2008 Leo Laporte started broadcasting live video from the TWiT Brick House in Petaluma, CA. This video allows viewers to watch the creation process of all of the TWiT netcasts and enables them to interact with Leo through one of the associated chats.", thumb=R('icon-twitlive.png')))

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1WEEK).xpath('//array/string'):
		(title, video_feed, audio_feed, cover, x) = feed.text.split('|',4)

		if video_feed != '':
			oc.add(DirectoryObject(key=Callback(Show, title=title, url=video_feed), title=title, thumb=Callback(Cover, url=cover, media='video', feed=video_feed)))

	return oc

####################################################################################################
def MainMenuAudio():

	oc = ObjectContainer()

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1WEEK).xpath('//array/string'):
		(title, video_feed, audio_feed, cover, x) = feed.text.split('|',4)

		if audio_feed != '':
			oc.add(DirectoryObject(key=Callback(Show, title=title, url=audio_feed), title=title, thumb=Callback(Cover, url=cover, media='audio', feed=video_feed)))

	return oc

####################################################################################################
def Show(title, url):

	oc = ObjectContainer(title2=title)



	return oc

####################################################################################################
def Cover(url, media, feed):

	if feed == '':
		show_abbr = 'twit'
	else:
		show_abbr = feed.split('.tv/',1)[1].split('_',1)[0]

	try:
		data = HTTP.Request(COVER_URL % (show_abbr, media), cacheTime=CACHE_1MONTH).content
		return DataObject(data, 'image/jpeg')
	except:
		try:
			data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
			return DataObject(data, 'image/jpeg')
		except:
			pass

	return Redirect(R(ICON))
