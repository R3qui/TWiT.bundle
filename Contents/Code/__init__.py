SHOWS_XML = "http://static.twit.tv/ShiftKeySoftware/rssFeeds.plist"
ITUNES_NAMESPACE = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
COVER_URL = "http://leoville.tv/podcasts/coverart/%s600%s.jpg"
LIVE_URLS = {
	'BitGravity 400 Kbps': 'http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/twit/live/low/playlist.m3u8',
	'BitGravity 1 Mbps': 'http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/twit/live/high/playlist.m3u8',
	'Ustream': 'http://iphone-streaming.ustream.tv/ustreamVideo/1524/streams/live/playlist.m3u8',
	'Justin.tv': 'http://usher.justin.tv/stream/multi_playlist/twit.m3u8',
	'Flosoft.biz': 'http://hls.twit.tv:1935/flosoft/smil:twitStream.smil/playlist.m3u8'
}

DATE_FORMAT = "%a, %d %b %Y"
RE_EP_TITLE = Regex('\s(?=[0-9]+:)')
RE_EP_NUMBER = Regex('\s([0-9]+)(:|$)')
RE_EP_URL = Regex('^http://twit\.tv/[^/]+/\d+$')

HLS_COMPAT = ('iOS', 'Android', 'Roku', 'Safari', 'MacOSX', 'Windows', 'Plex Home Theater')

####################################################################################################
def Start():

	ObjectContainer.title1 = "TWiT.TV"
	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler('/video/twittv', "TWiT.TV")
def MainMenu():

	oc = ObjectContainer(no_cache=True)

	# Add TWiT Live entry
	if Client.Platform in HLS_COMPAT:
		oc.add(LiveStream(hls_provider=Prefs['hls_provider']))

	retired_shows = RetiredShows()

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1WEEK).xpath('//array/string'):
		(title, video_feed, audio_feed, cover, x) = feed.text.split('|',4)

		if video_feed != '' and title not in retired_shows:
			show_abbr = video_feed.split('.tv/',1)[1].split('_',1)[0]

			oc.add(DirectoryObject(
				key = Callback(Show, title=title, url=video_feed, show_abbr=show_abbr, cover=cover, media='video'),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(url=[COVER_URL % (show_abbr, 'video'), cover])
			))

	if Client.Platform in HLS_COMPAT:
		oc.add(PrefsObject(title='Preferences...'))

	return oc

####################################################################################################
@route('/video/twittv/show', allow_sync = True)
def Show(title, url, show_abbr, cover, media):

	oc = ObjectContainer(title2=title)

	for episode in XML.ElementFromURL(url).xpath('//item'):
		if not episode.xpath('./enclosure/@type')[0].startswith('video/'):
			continue

		full_title = episode.xpath('./title/text()')[0]

		try:
			episode_title = RE_EP_TITLE.split(full_title, 1)[1]
		except:
			episode_title = full_title

		try:
			episode_number = RE_EP_NUMBER.search(full_title).group(1)
		except:
			continue

		url = episode.xpath('./comments/text()')[0]

		if not RE_EP_URL.search(url):
			# Not every show has short urls available, fix the ones that don't
			if show_abbr == 'floss':
				show_url = 'show/floss-weekly'
			elif show_abbr == 'htg':
				show_url = 'show/home-theater-geeks'
			elif show_abbr == 'ipad':
				show_url = 'show/ipad-today'
			elif show_abbr == 'natn':
				show_url = 'show/the-social-hour'
			else:
				show_url = show_abbr

			url = 'http://twit.tv/%s/%s' % (show_url, episode_number)

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

		oc.add(EpisodeObject(
			url = url,
			show = title,
			title = episode_title,
			absolute_index = int(episode_number),
			summary = summary,
			originally_available_at = Datetime.ParseDate(date).date(),
			duration = duration,
			thumb = Resource.ContentsOfURLWithFallback(url=[COVER_URL % (show_abbr, media), cover])
		))

	return oc

####################################################################################################
def RetiredShows():

	page = HTML.ElementFromURL('http://twit.tv/shows', cacheTime=CACHE_1MONTH)
	shows = page.xpath('//div[@id="quicktabs_tabpage_3_1"]//a/text()')
	shows.extend(['FourCast Weekly', 'Game On', 'Net @ Night', 'THT: Tech History Today', 'Recent TWiT VIDEO'])

	return shows

####################################################################################################
def LiveStream(hls_provider='Ustream', include_container=False):

	vco = VideoClipObject(
		key = Callback(LiveStream, hls_provider=hls_provider, include_container=True),
		rating_key = LIVE_URLS[hls_provider],
		title = 'Watch TWiT Live',
		thumb = R('icon-twitlive.png'),
		items = [
			MediaObject(
				video_resolution = 'sd',
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
