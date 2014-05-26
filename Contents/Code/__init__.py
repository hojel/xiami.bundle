# -*- coding: utf-8 -*-

###################################################################################################

PLUGIN_TITLE     = "xiami"
PLUGIN_PREFIX    = "/music/xiami"
ICON_DEFAULT     = "icon-default.png"
ROOT_URL         = "http://www.xiami.com"
USER_AGENT       = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:10.0.2) Gecko/20100101 Firefox/10.0.2"

SUBGENRE_URL     = ROOT_URL+"/genre/{0:s}s/sid/{1:s}/page/{2:s}"

GENRE_DATA       = 'genre.json'

###################################################################################################
def Start():
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

  ObjectContainer.title1     = PLUGIN_TITLE
  ObjectContainer.view_group = "InfoList"
  DirectoryObject.thumb      = R(ICON_DEFAULT)

  #HTTP.CacheTime = CACHE_1DAY
  #HTTP.Headers['User-Agent'] = USER_AGENT
  #JSON.Headers['User-Agent'] = USER_AGENT

####################################################################################################
@handler(PLUGIN_PREFIX, PLUGIN_TITLE, thumb = ICON_DEFAULT)
def MusicMainMenu():
  oc = ObjectContainer(view_group="List")
  oc.add(DirectoryObject(key=Callback(BangAlbumsMenu, type='new'), title=L('New Albums')))
  oc.add(DirectoryObject(key=Callback(BangAlbumsMenu, type='hot'), title=L('Hot Albums')))
  oc.add(DirectoryObject(key=Callback(ChartMenu), title=L('Charts')))
  oc.add(DirectoryObject(key=Callback(GenreTop), title=L('Genre')))
  oc.add(DirectoryObject(key=Callback(SearchMenu), title=L('Search by')))
  oc.add(DirectoryObject(key=Callback(JumpMenu), title=L('Jump to')))
  #oc.add(PrefsObject(title=L('Preference')))
  return oc

@route(PLUGIN_PREFIX+'/genre')
def GenreTop():
  userdata = Resource.Load(GENRE_DATA)
  GenreInfo = JSON.ObjectFromString(userdata)

  oc = ObjectContainer(title2="Genre", view_group="List")
  for title, data in GenreInfo.iteritems():
    oc.add(DirectoryObject(key=Callback(GenreList, id=data['id']), title=title))
  return oc

@route(PLUGIN_PREFIX+'/genre/{id}')
def GenreList(id):
  userdata = Resource.Load(GENRE_DATA)
  GenreInfo = JSON.ObjectFromString(userdata)

  oc = ObjectContainer(title2="Genre", view_group="List")
  for title, data in GenreInfo.iteritems():
    if data['id'] == int(id):
      Log.Debug('Subgenre for '+title)
      for title2, data2 in data['sub'].iteritems():
        oc.add(DirectoryObject(key=Callback(SubGenreList, id=data2['id']), title=title2))
      break
  return oc

@route(PLUGIN_PREFIX+'/subgenre/{id}')
def SubGenreList(id):
  oc = ObjectContainer(title2="Genre", view_group="List")
  oc.add(DirectoryObject(key=Callback(SubGenreList2, id=id, domain='artist', pageNum='1'), title=L('Artist')))
  oc.add(DirectoryObject(key=Callback(SubGenreList2, id=id, domain='album', pageNum='1'), title=L('Album')))
  oc.add(DirectoryObject(key=Callback(SubGenreList2, id=id, domain='song', pageNum='1'), title=L('Song')))
  return oc

@route(PLUGIN_PREFIX+'/subgenre/{id}/{domain}/{pageNum}')
def SubGenreList2(id, domain, pageNum):
  oc = ObjectContainer(title2="Genre", view_group="List")
  url = SUBGENRE_URL.format(domain, id, pageNum)
  html = HTML.ElementFromURL(url, headers={'User-Agent':USER_AGENT})

  domain2 = 'songwrapper song' if domain == 'song' else domain
  for item in html.xpath("//div[@class='%s']" % domain2):
    thumb = item.xpath(".//div[@class='image']/img")[0].get('src')
    node = item.xpath(".//div[@class='info']/p/strong/a")[0]
    title = node.text
    n_id = node.get('href').rsplit('/')[-1]
    if domain == 'artist':
      #oc.add(ArtistObject(key=Callback(ArtistAlbums, artistid=n_id), title=title, thumb=thumb))
      oc.add(DirectoryObject(key=Callback(ArtistAlbums, artistid=n_id), title=title, thumb=thumb))
    elif domain == 'album':
      #oc.add(AlbumObject(key=Callback(AlbumTracks, albumid=n_id), title=title, thumb=thumb))
      oc.add(DirectoryObject(key=Callback(AlbumTracks, albumid=n_id), title=title, thumb=thumb))
    elif domain == 'song':
      oc.add(DirectoryObject(key=Callback(GetTrack, songid=n_id), title=title, thumb=thumb))
  # navigation
  nextpg_node = html.xpath("//a[@class='p_redirect_l']")
  if nextpg_node:
    n_url = nextpg_node[0].get('href')
    oc.add(NextPageObject(key=Callback(SubGenreList2, domain=domain, id=id, pageNum=n_url.rsplit('/')[-1]), title="Next Page"))
  return oc

@route(PLUGIN_PREFIX+'/search')
def SearchMenu():
  oc = ObjectContainer(title2="Search", view_group="List")
  oc.add(InputDirectoryObject(key=Callback(Search, domain='artist'), title=L('Artist'), prompt=L('Name')))
  oc.add(InputDirectoryObject(key=Callback(Search, domain='album'), title=L('Album'), prompt=L('Name')))
  return oc

@route(PLUGIN_PREFIX+'/search/{domain}')
def Search(domain, query=''):
  Log.Debug("Search %s, %s" % (domain, query))
  oc = ObjectContainer(title2="Search", view_group="List")

  url = ROOT_URL+"/search/%s?key=%s" % (domain, String.Quote(query, usePlus=True))
  Log.Debug("Search %s" % url)
  html = HTML.ElementFromURL(url, headers={'User-Agent':USER_AGENT})

  for item in html.xpath("//div[contains(@class, '%sBlock_list')]//li" % domain):
    title = ''.join( item.xpath(".//p[@class='name']//text()") )
    thumb = item.xpath(".//img")[0].get('src')
    if domain == 'artist':
      url = item.xpath(".//a[@class='artist100']")[0].get('href')
      artistid = url.split('/')[-1]
      #oc.add(ArtistObject(key=Callback(ArtistAlbums, artistid=artistid), title=title, thumb=thumb))
      oc.add(DirectoryObject(key=Callback(ArtistAlbums, artistid=artistid), title=title, thumb=thumb))
    elif domain == 'album':
      url = item.xpath(".//a[@class='CDcover100']")[0].get('href')
      albumid = url.split('/')[-1]
      #oc.add(AlbumObject(key=Callback(AlbumTracks, albumid=albumid), title=title, thumb=thumb))
      oc.add(DirectoryObject(key=Callback(AlbumTracks, albumid=albumid), title=title, thumb=thumb))

  return oc

@route(PLUGIN_PREFIX+'/jump')
def JumpMenu():
  oc = ObjectContainer(title2="Jump", view_group="List")
  oc.add(InputDirectoryObject(key=Callback(JumpArtist), title=L('Artist'), prompt="ID"))
  oc.add(InputDirectoryObject(key=Callback(JumpAlbum), title=L('Album'), prompt="ID"))
  #oc.add(InputDirectoryObject(key=Callback(JumpCollect), title=L('Collect'), prompt="ID"))
  return oc

@route(PLUGIN_PREFIX+'/jump/artist')
def JumpArtist(query=''):
  Log.Debug("Jump to Artist %s" % query)
  return Redirect(ArtistAlbums(artistid=query))

@route(PLUGIN_PREFIX+'/jump/album')
def JumpAlbum(query=''):
  Log.Debug("Jump to Album %s" % query)
  return Redirect(AlbumTracks(albumid=query))

####################################################################################################
@route(PLUGIN_PREFIX+'/bang-albums/{type}')
def BangAlbumsMenu(type):
  oc = ObjectContainer(title2="Bang-Albums", view_group="List")
  oc.add(DirectoryObject(key=Callback(BangAlbums, type=type, style='all'), title=L('All')))
  oc.add(DirectoryObject(key=Callback(BangAlbums, type=type, style='huayu'), title=L('Chinese')))
  oc.add(DirectoryObject(key=Callback(BangAlbums, type=type, style='oumei'), title=L('West')))
  oc.add(DirectoryObject(key=Callback(BangAlbums, type=type, style='ri'), title=L('Japan')))
  oc.add(DirectoryObject(key=Callback(BangAlbums, type=type, style='han'), title=L('Korea')))
  return oc

@route(PLUGIN_PREFIX+'/bang-albums/{type}/{style}')
def BangAlbums(type, style):
  oc = ObjectContainer(view_group="List")

  url = ROOT_URL+'/web/bang-albums?type=%s&style=%s' % (type, style)
  data = JSON.ObjectFromURL(url, headers={'User-Agent':USER_AGENT})
  for item in data['albums']:
    title = unescape_name(item['album_name'])
    #oc.add(AlbumObject(key=Callback(AlbumTracks, albumid=item['album_id']), title=title, thumb=item['logo']))
    oc.add(DirectoryObject(key=Callback(AlbumTracks, albumid=item['album_id']), title=title, thumb=item['logo']))

  return oc

@route(PLUGIN_PREFIX+'/charts')
def ChartMenu():
  oc = ObjectContainer(title2="Charts", view_group="List")
  oc.add(DirectoryObject(key=Callback(Chart, type='all'), title=L('All')))
  oc.add(DirectoryObject(key=Callback(Chart, type='huayu'), title=L('Chinese')))
  oc.add(DirectoryObject(key=Callback(Chart, type='oumei'), title=L('West')))
  oc.add(DirectoryObject(key=Callback(Chart, type='rihan'), title=L('Japan/Korea')))
  oc.add(DirectoryObject(key=Callback(Chart, type='billboard'), title=L('Billboard')))
  oc.add(DirectoryObject(key=Callback(Chart, type='uk'), title=L('UK')))
  oc.add(DirectoryObject(key=Callback(Chart, type='oricon'), title=L('Oricon')))
  oc.add(DirectoryObject(key=Callback(Chart, type='mnet'), title=L('Mnet')))
  return oc

@route(PLUGIN_PREFIX+'/chart/{type}')
def Chart(type):
  oc = ObjectContainer(view_group="List")

  url = ROOT_URL+'/web/get-songs?type=%s&rtype=bang&id=0' % type
  data = JSON.ObjectFromURL(url, headers={'User-Agent':USER_AGENT})
  for item in data['data']:
    thumb = item['cover'],
    thumb = thumb[ thumb.rfind('http://'): ]
    oc.add(TrackObject(
      key=Callback(GetTrack, songid=item['id']),
      rating_key=item['src'],
      title=unescape_name(item['title']),
      artist=item['author'],
      thumb=thumb,
      items=[ MediaObject(
          parts=[ PartObject(key=Callback(PlayAudio, url=item['src'])) ],
          container=Container.MP3,
          audio_codec=AudioCodec.MP3,
          audio_channels=2) ]
    ))

  return oc

####################################################################################################
@route(PLUGIN_PREFIX+'/artist/{artistid}')
def ArtistAlbums(artistid):
  url = ROOT_URL+'/app/android/artist?id='+artistid
  data = JSON.ObjectFromURL(url)
  totalCnt = int(data['artist']['albums_count'])
  return ArtistAlbums2(data['artist']['name'], artistid, totalCnt, '0')

@route(PLUGIN_PREFIX+'/artist/{artistid}/{totalCnt}/{pageNum}')
def ArtistAlbums2(name, artistid, totalCnt, pageNum):
  dispPerPage = 20
  pageNum2 = 1 if pageNum == '0' else int(pageNum)

  oc = ObjectContainer(title2=name, view_group="List")

  url = ROOT_URL+'/app/android/artist-albums?id=%s&page=%d' % (artistid, pageNum2)
  data = JSON.ObjectFromURL(url, headers={'User-Agent':USER_AGENT})
  for item in data['albums']:
    title = unescape_name(item['title'])
    #oc.add(AlbumObject(key=Callback(AlbumTracks, albumid=item['album_id']), title=title, thumb=item['album_logo']))
    oc.add(DirectoryObject(key=Callback(AlbumTracks, albumid=item['album_id']), title=title, thumb=item['album_logo']))
  # navigation
  if (pageNum2*dispPerPage) < int(totalCnt):
    oc.add(NextPageObject(key=Callback(ArtistAlbums2, name=name, artistid=artistid, totalCnt=totalCnt, pageNum=pageNum2+1), title="Next Page"))

  return oc

####################################################################################################
# URL Service is not used to play song witout prompt
@route(PLUGIN_PREFIX+'/album/{albumid}')
def AlbumTracks(albumid):
  url = ROOT_URL+'/app/android/album?id='+albumid
  data = JSON.ObjectFromURL(url, headers={'User-Agent':USER_AGENT})

  album_title = unescape_name(data['album']['title'])
  oc = ObjectContainer(title2=album_title, view_group="List")
  for item in data['album']['songs']:
    title = unescape_name(item['name'])
    oc.add(TrackObject(
      key=Callback(GetTrack, songid=item['song_id']),
      rating_key=item['location'],
      title=unescape_name(item['name']),
      artist=item['artist_name'],
      thumb=item['album_logo'],
      items=[ MediaObject(
          parts=[ PartObject(key=Callback(PlayAudio, url=String.Encode(item['location']))) ],
          container=Container.MP3,
          audio_codec=AudioCodec.MP3,
          audio_channels=2) ]
    ))

  return oc

@route(PLUGIN_PREFIX+'/song/{songid}')
def GetTrack(songid):
  url = ROOT_URL+'/app/iphone/song/id/'+songid
  data = JSON.ObjectFromURL(url, headers={'User-Agent':USER_AGENT})
  Log.Debug('MP3 URL '+data['location'])

  track = TrackObject(
       key=Callback(GetTrack, songid=songid),
       rating_key=data['location'],
       title=unescape_name(data['title']),
       artist=data['artist_name'],
       thumb=data['album_logo'],
       items=[ MediaObject(
          parts=[ PartObject(key=Callback(PlayAudio, url=String.Encode(data['location']))) ],
          container=Container.MP3,
          audio_codec=AudioCodec.MP3,
          audio_channels=2) ] )
  return track

@route(PLUGIN_PREFIX+'/play/{url}')
def PlayAudio(url):
  return Redirect(String.Decode(url))

def unescape_name(s):
  return s.replace('&#039;',"'")
