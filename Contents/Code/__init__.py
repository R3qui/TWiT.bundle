import re

SHOWS_XML = "http://static.twit.tv/rssFeeds.plist"
ITUNES_NAMESPACE = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
COVER_URL = "http://leoville.tv/podcasts/coverart/%s600%s.jpg"

DATE_FORMAT = "%a, %d %b %Y"
ICON = "icon-default.png"
ART = "art-default.jpg"

####################################################################################################
def Start():

	Plugin.AddPrefixHandler("/video/twittv", MainMenuVideo, "TWiT.TV", ICON, ART)
#	Plugin.AddPrefixHandler("/music/twittv", MainMenuAudio, "TWiT.TV", ICON, ART)

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
	oc.add(VideoClipObject(
		url = "twit://livestream",
		title = "TWiT Live",
		thumb = R('icon-twitlive.png')
	))

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1WEEK).xpath('//array/string'):
		(title, video_feed, audio_feed, cover, x) = feed.text.split('|',4)

		if video_feed != '':
			show_abbr = video_feed.split('.tv/',1)[1].split('_',1)[0]
			oc.add(DirectoryObject(key=Callback(Show, title=title, url=video_feed, show_abbr=show_abbr, cover=cover, media='video'), title=title, thumb=Callback(Cover, url=cover, media='video', show_abbr=show_abbr)))

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

			oc.add(DirectoryObject(key=Callback(Show, title=title, url=audio_feed, show_abbr=show_abbr, cover=cover, media='audio'), title=title, thumb=Callback(Cover, url=cover, media='audio', show_abbr=show_abbr)))

	return oc

####################################################################################################
def Show(title, url, show_abbr, cover, media):

	oc = ObjectContainer(title2=title, view_group='InfoList')

	for episode in XML.ElementFromURL(url).xpath('//item'):
		full_title = episode.xpath('./title')[0].text

		try:
			episode_title = re.split('\s(?=[0-9]+:)', full_title)[1]
		except:
			episode_title = full_title

		episode_number = re.search('\s([0-9]+)(:|$)', full_title).group(1)
		url = 'http://twit.tv/%s%s' % (show_abbr, episode_number)

		try:
			summary = episode.xpath('./itunes:subtitle', namespaces=ITUNES_NAMESPACE)[0].text
		except:
			summary = None

		date = episode.xpath('./pubDate')[0].text

		try:
			duration = episode.xpath('./itunes:duration', namespaces=ITUNES_NAMESPACE)[0].text
		except:
			duration = None

		oc.add(VideoClipObject(
			url = url,
			title = episode_title,
			summary = summary,
			originally_available_at = Datetime.ParseDate(date).date(),
			duration = TimeToMs(duration),
			thumb = Callback(Cover, url=cover, media=media, show_abbr=show_abbr)
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

####################################################################################################
def TimeToMs(timecode):

	seconds = 0

	try:
		duration = timecode.split(':')
		duration.reverse()

		for i in range(0, len(duration)):
			seconds += int(duration[i]) * (60**i)
	except:
		pass

	return seconds * 1000
