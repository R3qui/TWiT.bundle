import re

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
	ObjectContainer.view_group = "List"
	DirectoryItem.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def MainMenuVideo():

	oc = ObjectContainer()

	# Add TWiT Live entry
	oc.add(VideoClipObject(key=WebVideoURL(TWIT_LIVE), rating_key=TWIT_LIVE, title="TWiT Live", thumb=R('icon-twitlive.png')))

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1WEEK).xpath('//array/string'):
		(title, video_feed, audio_feed, cover, x) = feed.text.split('|',4)

		if video_feed != '':
			show_abbr = video_feed.split('.tv/',1)[1].split('_',1)[0]
			oc.add(DirectoryObject(key=Callback(Show, title=title, url=video_feed, show_abbr=show_abbr), title=title, thumb=Callback(Cover, url=cover, media='video', show_abbr=show_abbr)))

	return oc

####################################################################################################
def MainMenuAudio():

	oc = ObjectContainer()

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1WEEK).xpath('//array/string'):
		(title, video_feed, audio_feed, cover, x) = feed.text.split('|',4)

		if audio_feed != '':
			if video_feed != '':
				show_abbr = video_feed.split('.tv/',1)[1].split('_',1)[0]
			else:
				show_abbr = 'twit'

			oc.add(DirectoryObject(key=Callback(Show, title=title, url=audio_feed), title=title, thumb=Callback(Cover, url=cover, media='audio', show_abbr=show_abbr)))

	return oc

####################################################################################################
def Show(title, url, show_abbr):

	oc = ObjectContainer(title2=title, view_group='InfoList')

	for episode in XML.ElementFromURL(url).xpath('//item'):
		title = episode.xpath('./title')[0].text
		episode_number = re.search('\s([0-9]+)(:|$)', title).group(1)
		url = 'http://twit.tv/%s%s' % (show_abbr, episode_number)

		oc.add(VideoClipObject(
			url = url,
			title = title
		))

	return oc

####################################################################################################
def Cover(url, media, show_abbr):

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
