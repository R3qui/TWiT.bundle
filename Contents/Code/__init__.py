SHOWS_XML = "http://static.twit.tv/ShiftKeySoftware/rssFeeds.plist"
ITUNES_NAMESPACE = {'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
COVER_URL = "http://leoville.tv/podcasts/coverart/%s600%s.jpg"
LIVE_URL = "http://ustream.tv/leolaporte"

DATE_FORMAT = "%a, %d %b %Y"
ICON = "icon-default.png"
ART = "art-default.jpg"

RE_EP_TITLE = Regex('\s(?=[0-9]+:)')
RE_EP_NUMBER = Regex('\s([0-9]+)(:|$)')

####################################################################################################
def Start():

	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")

	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = "TWiT.TV"
	ObjectContainer.view_group = "List"
	DirectoryItem.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler('/video/twittv', "TWiT.TV", art = ART, thumb = ICON)
def MainMenu():

	oc = ObjectContainer()

	# Add TWiT Live entry
	try:
		oc.add(VideoClipObject(
			url = LIVE_URL,
			title = "Watch TWiT Live",
			thumb = R('icon-twitlive.png')
		))
	except:
		Log('Adding live stream item failed.')
		pass

	retired_shows = RetiredShows()

	for feed in XML.ElementFromURL(SHOWS_XML, cacheTime=CACHE_1WEEK).xpath('//array/string'):
		(title, video_feed, audio_feed, cover, x) = feed.text.split('|',4)

		if video_feed != '' and title not in retired_shows:
			show_abbr = video_feed.split('.tv/',1)[1].split('_',1)[0]
			oc.add(DirectoryObject(key=Callback(Show, title=title, url=video_feed, show_abbr=show_abbr, cover=cover, media='video'), title=title, thumb=Callback(Cover, url=cover, media='video', show_abbr=show_abbr)))

	return oc

####################################################################################################
@route('/video/twittv/show', allow_sync = True)
def Show(title, url, show_abbr, cover, media):

	oc = ObjectContainer(title2=title, view_group='InfoList')

	for episode in XML.ElementFromURL(url).xpath('//item'):
		if not episode.xpath('./enclosure')[0].get('type').startswith('video/'):
			continue

		full_title = episode.xpath('./title')[0].text

		try:
			episode_title = RE_EP_TITLE.split(full_title, 1)[1]
		except:
			episode_title = full_title

		episode_number = RE_EP_NUMBER.search(full_title).group(1)

		# Not every show has short urls available, fix the ones that don't
		if show_abbr == 'floss':
			show_url = 'show/floss-weekly/'
		elif show_abbr == 'htg':
			show_url = 'show/home-theater-geeks/'
		elif show_abbr == 'ipad':
			show_url = 'show/ipad-today/'
		elif show_abbr == 'natn':
			show_url = 'show/the-social-hour/'
		else:
			show_url = show_abbr

		url = 'http://twit.tv/%s%s' % (show_url, episode_number)

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

####################################################################################################
def RetiredShows():

	page = HTML.ElementFromURL('http://twit.tv/shows', cacheTime=CACHE_1MONTH)
	shows = page.xpath('//div[@id="quicktabs_tabpage_3_1"]//a/text()')
	shows.extend(['FourCast Weekly', 'Game On', 'Net @ Night', 'THT: Tech History Today'])

	return shows
