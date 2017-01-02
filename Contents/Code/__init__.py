SHOWS_XML = "http://static.twit.tv/ShiftKeySoftware/rssFeeds.plist"
ITUNES_NAMESPACE = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
LIVE_URLS = {
	'Flosoft.biz': 'http://hls.twit.tv/flosoft/smil:twitStream.smil/playlist.m3u8'
}

####################################################################################################
def Start():

	ObjectContainer.title1 = 'TWiT.TV'
	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler('/video/twittv', 'TWiT.TV')
def MainMenu():

	oc = ObjectContainer(no_cache=True)

	# TWiT Live
	oc.add(LiveStream(hls_provider=Prefs['hls_provider']))

	retired_shows = RetiredShows()

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1DAY).xpath('//array/string'):

		(title, video_feed, audio_feed, cover, junk) = feed.text.split('|', 4)

		if video_feed != '' and title not in retired_shows:

			oc.add(DirectoryObject(
				key = Callback(Show, title=title, url=video_feed, cover=cover),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(url=cover)
			))

	oc.add(PrefsObject(title='Preferences...'))

	return oc

####################################################################################################
@route('/video/twittv/show', allow_sync=True)
def Show(title, url, cover):

	oc = ObjectContainer(title2=title)

	for episode in XML.ElementFromURL(url).xpath('//item'):

		if not episode.xpath('./enclosure/@type')[0].startswith('video/'):
			continue

		url = episode.xpath('./comments/text()')[0]
		title = episode.xpath('./title/text()')[0]

		try:
			summary = episode.xpath('./itunes:summary/text()', namespaces=ITUNES_NAMESPACE)[0]
			summary = String.StripTags(summary)
		except:
			summary = None

		date = episode.xpath('./pubDate/text()')[0]

		try:
			duration = episode.xpath('./itunes:duration/text()', namespaces=ITUNES_NAMESPACE)[0]
			duration = Datetime.MillisecondsFromString(duration)
		except:
			duration = None

		oc.add(VideoClipObject(
			url = url,
			title = title,
			summary = summary,
			originally_available_at = Datetime.ParseDate(date).date(),
			duration = duration,
			thumb = Resource.ContentsOfURLWithFallback(url=cover)
		))

	return oc

####################################################################################################
def RetiredShows():

	shows = []
	#shows.extend(['The Giz Wiz'])

	return shows

####################################################################################################
def LiveStream(hls_provider='Flosoft.biz', include_container=False):

	if hls_provider not in LIVE_URLS:
		hls_provider = 'Flosoft.biz'

	vco = VideoClipObject(
		key = Callback(LiveStream, hls_provider=hls_provider, include_container=True),
		rating_key = LIVE_URLS[hls_provider],
		title = 'Watch TWiT Live',
		thumb = R('icon-twitlive.png'),
		items = [
			MediaObject(
				video_resolution = '480',
				parts = [
					PartObject(key=HTTPLiveStreamURL(LIVE_URLS[hls_provider]))
				]
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[vco])
	else:
		return vco
