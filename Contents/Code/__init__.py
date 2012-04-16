#Live Music Archive (from archive.org) plugin for plex media server

# copyright 2009 Billy Joe Poettgen
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# background image is from http://commons.wikimedia.org/wiki/File:Justice_in_concert.jpg
# icon/cover by Jay Del Turco

import string
import datetime

RECENT_SHOWS = "http://archive.org/search.php?query=collection%3Aetree&sort=-publicdate"
MOST_DOWNLOADED = "http://www.archive.org/search.php?query=%28%28collection%3Aetree%20OR%20mediatype%3Aetree%29%20AND%20NOT%20collection%3AGratefulDead%29%20AND%20-mediatype%3Acollection&sort=-downloads"
MOST_DOWNLOADED_WEEK = "http://www.archive.org/search.php?query=%28%28collection%3Aetree%20OR%20mediatype%3Aetree%29%20AND%20NOT%20collection%3AGratefulDead%29%20AND%20-mediatype%3Acollection&sort=-week"
ARTISTS_URL = "http://www.archive.org/advancedsearch.php?q=mediatype%3Acollection+collection%3Aetree&fl[]=creator&fl[]=identifier&sort[]=identifier+asc&sort[]=&sort[]=&rows=50000&page=1&fmt=xml&xmlsearch=Search#raw"
BASE_URL = "http://archive.org"

###################################################################################################
def Start():
  Plugin.AddPrefixHandler('/music/LMA', MainMenu, 'Live Music Archive', 'icon-default.png', 'art-default.jpg')
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  ObjectContainer.title1 = 'Live Music Archive'
  ObjectContainer.content = 'Items'
  ObjectContainer.art = R('art-default.jpg')
  DirectoryObject.thumb = R('icon-default.png')
  AlbumObject.thumb = R('icon-default.png')
  #AlbumObject.art = R('art-default.jpg')
  TrackObject.thumb = R('icon-default.png')
  HTTP.CacheTime = CACHE_1HOUR

###################################################################################################

def MainMenu():
  oc = ObjectContainer(view_group='List')
  oc.add(DirectoryObject(key=Callback(Letters), title="Browse Archive by Artist"))
  oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.LMA", title="Search the Live Music Archive", prompt="Search for...", thumb=R('icon-default.png')))
  todayURL = TodayURL()
  oc.add(DirectoryObject(key=Callback(ShowList, title2="This Day in History", pageURL=todayURL), title="Shows This Day in History"))
  oc.add(DirectoryObject(key=Callback(ShowList, title2="Recently Added Shows", pageURL=RECENT_SHOWS), title="Most Recently Added Shows"))
  oc.add(DirectoryObject(key=Callback(ShowList, title2="Most Downloaded", pageURL=MOST_DOWNLOADED), title="Most Downloaded Shows"))
  oc.add(DirectoryObject(key=Callback(ShowList, title2="Last Week", pageURL=MOST_DOWNLOADED_WEEK), title="Most Downloaded Shows Last Week"))
  oc.add(DirectoryObject(key=Callback(Staff), title="Staff Picks"))
  
  if iTunesPage() != None:
    oc.add(ObjectDirectory(key=Callback(iTunes), title="Find Shows for Artists in my iTunes Library"))
    oc.add(PrefsObject("Preferences...",
           summary="No PMS instance with a valid iTunes library at this address (default: localhost)\n Please enter the IP address of a PMS instance sharing an iTunes library.",
           thumb=S('Gear.png')))
  else:
    oc.add(PrefsObject(title="Preferences...", thumb=S('Gear.png')))
  return oc

##################################################################################################

def Letters():
  oc = ObjectContainer(title2="Artists", view_group='List')
  oc.add(DirectoryObject(key=Callback(Artists, letter="#"), title="#"))
  for c in list(string.ascii_uppercase):
    oc.add(DirectoryObject(key=Callback(Artists, letter=c), title=c))

  return oc

##################################################################################################

def Artists(letter=None):
  oc = ObjectContainer(title2="Artists-%s" % letter, view_group='List')
  artistsList = XML.ElementFromURL(ARTISTS_URL, errors='ignore',)
  results = artistsList.xpath("/response//doc")
  for n in range(len(results)):
    identifier = artistsList.xpath("//doc[%i]/str[@name='identifier']/text()"  % (n+1))
    name = artistsList.xpath("//doc[%i]/arr[@name='creator']/str/text()"  % (n+1))
    if identifier != []:
      identifier = str(identifier[0])
    else:
      continue
    if name != []:
      name = str(name[0])
    else:
      continue
    if letter=="#":
      for n in list(string.digits):
        if identifier[0] == n:
          pageURL= "http://www.archive.org/search.php?query=collection%3A" + identifier + "&sort=-date&page=1"
          oc.add(DirectoryObject(key=Callback(ShowList, pageURL=pageURL, title2=name, isArtistPage=True, identifier=identifier), title=name))
    else:
      if identifier[0] == letter:
        pageURL= "http://www.archive.org/search.php?query=collection%3A" + identifier + "&sort=-date&page=1"
        oc.add(DirectoryObject(key=Callback(ShowList, title2=name, pageURL=pageURL, isArtistPage=True, identifier=identifier, artist=name), title=name))

  return oc

##################################################################################################

def ShowList(title2, pageURL=None, isArtistPage=False, identifier=None, query=None, thumbs=None, artist=None):
  oc = ObjectContainer(title2=title2, view_group='InfoList')
  if thumbs == None:
    thumbs = R('icon-default.png')
  if query != None:
    query = String.URLEncode(query)
    pageURL="http://www.archive.org/search.php?query="+query+"%20AND%20collection%3Aetree"
  
  
  showsList = HTML.ElementFromURL(pageURL, errors='ignore')
  if showsList != None:

    # auto detect show numbers and split by year if high
    if isArtistPage == True:
      numShows = showsList.xpath("//div[3]//tr[2]//td[1]//b[2]//text()")
      if numShows[0] == '0':
        return ObjectContainer(header='Live Music Archive', message="No concerts found.")
      if numShows != []:
        numShows = int(numShows[0].replace(",",""))
        if numShows >= 51:
          # get the years list
          yearsPage = HTML.ElementFromURL("http://www.archive.org/browse.php?collection=" + identifier + "&field=year", errors="ignore")
          years = yearsPage.xpath("//table[@id='browse']//ul//a/text()")
          yearURLs = yearsPage.xpath("//table[@id='browse']//ul//a/@href")
          for year, url in zip(years, yearURLs):
            oc.add(DirectoryObject(key=Callback(ShowList, title2=str(year), pageURL="http://www.archive.org" + url + "&sort=date", artist=artist), title=str(year), thumb=thumbs))
          return oc


    showURLs = showsList.xpath("//a[@class='titleLink']/@href")
    showTitles = showsList.xpath("//a[@class='titleLink']")
    # pain in my fucking ass roundabout way to get proper show titles for artists split by date
    titles = []
    summaries = []
    ratings = []
    for i in range(len(showTitles)):
      y = showsList.xpath("//table[@class='resultsTable']//tr[%i]/td[2]/a[1]//text()" % (i+1))
      # the +1 is because python list indexes start from 0 and indexes in xpath start at 1
      title = ''.join(y)
      titles.append(title)
      
      x = showsList.xpath("//table[@class='resultsTable']//tr[%i]//td[@class='hitCell']/text()" % (i+1))[1]
      # the +1 is because python list indexes start from 0 and indexes in xpath start at 1
      summary = ''.join(x)
      summaries.append(summary)
      
      w = showsList.xpath("//table[@class='resultsTable']//tr[%i]//img[contains(@src, '/images/stars')]" % (i+1))
      # the +1 is because python list indexes start from 0 and indexes in xpath start at 1
      try:
        rating = float(w[0].get('title').split(' ')[0])*2
      except:
        rating = None
      ratings.append(rating)
      
    for url, title, summary, rating in zip(showURLs, titles, summaries, ratings):
      # for artists in the search results
      if showsList.xpath("//a[@class='titleLink'][@href='%s']/parent::td/preceding-sibling::td/img[@alt='[collection]']" %url):
        pageURL= "http://www.archive.org/search.php?query=collection%3A" + url.replace("/details/","") + "&sort=-date&page=1"
        oc.add(DirectoryObject(key=Callback(ShowList, pageURL=pageURL, title2=title, isArtistPage=True, identifier=url.replace("/details/",""), artist=artist),
          title=title))

      else:
        concertURL = ConcertURL(url)
        oc.add(AlbumObject(url=concertURL,  title=str(title), summary=summary, rating=rating, artist=artist))

    next = showsList.xpath("//a[text()='Next']/@href")
    if next != []:
      pageURL = "http://www.archive.org" + next[0]
      oc.add(DirectoryObject(key=Callback(ShowList, pageURL=pageURL, title2=title2, artist=artist), title="Next 50 Results"))
      
  if len(oc) == 0:
    return ObjectContainer(header='Live Music Archive', message='No shows listed.')

  return oc

##################################################################################################

def ConcertURL(url):
  return "http://www.archive.org" + url

##################################################################################################

def Staff():
  oc = ObjectContainer(title2="Staff Picks")
  page = HTML.ElementFromURL("http://www.archive.org/details/etree", errors="ignore")
  picks = page.xpath("//div[@id='picks']//a")
  for pick in picks:
    title = pick.text
    url = BASE_URL + pick.get('href')
    oc.add(AlbumObject(url=url, title=title, thumb=R('icon-default.png')))

  return oc

##################################################################################################

def iTunes():
# fuzzy matching way way way way way too slow (estimate 15 minutes for my library), cant even verify it works. exact matches only till plex framework can do the matching
  
  oc = ObjectContainer(title2="iTunes")

  itunesArtistsPage = itunesPage()
  itunesArtists = itunesArtistsPage.xpath('//Artist/@artist')
  itunesThumbs = itunesArtistsPage.xpath('//Artist/@thumb')
  
  LMAartistsURL = "http://www.archive.org/advancedsearch.php?q=mediatype%3Acollection+collection%3Aetree&fl[]=creator&fl[]=identifier&sort[]=identifier+asc&sort[]=&sort[]=&rows=50000&page=1&fmt=xml&xmlsearch=Search#raw"
  LMAartistsList = XML.ElementFromURL(LMAartistsURL, errors='ignore',)
  results = LMAartistsList.xpath("/response//doc")
  
  itunesDict = {}
  for itunesArtist, itunesThumb in zip(itunesArtists, itunesThumbs):
    itunesArtist = str(itunesArtist).lower().replace(" and ", "").replace("the ", "").replace(" ", "").translate(string.maketrans("",""), string.punctuation)
    itunesDict[itunesArtist] = itunesThumb
  
  for n in range(len(results)):
    identifier = LMAartistsList.xpath("//doc[%i]/str[@name='identifier']/text()"  % (n+1))
    LMAname = LMAartistsList.xpath("//doc[%i]/arr[@name='creator']/str/text()"  % (n+1))
    if identifier != []:
      identifier = str(identifier[0])
    else:
      continue
    if LMAname != []:
      LMAname = str(LMAname[0])
    else:
      continue
    
    
    strippedLMAname = LMAname.lower().replace(" and ", "").replace("the ", "").replace(" ", "").translate(string.maketrans("",""), string.punctuation)
    
    
    if strippedLMAname in itunesDict:
        pageURL= "http://www.archive.org/search.php?query=collection%3A" + identifier + "&sort=-date&page=1"
        thumb = "http://" + Prefs['itunesIP'] + ":32400" +  itunesDict[strippedLMAname]
        
        oc.add(DirectoryObject(key=Callback(ShowList, pageURL=pageURL, title2=LMAname, isArtistPage=True, identifier=identifier, thumbs=thumb), title=LMAname, thumb=thumb))
    
  return oc

##################################################################################################

def TodayURL():
  now = datetime.datetime.now()
  month = str(now.month)
  day = str(now.day)
  if now.month < 10:
    month = '0' + month
  if now.day < 10:
    day = '0' + day
  today_URL = "http://www.archive.org/search.php?query=collection:etree%20AND%20%28date:19??-"+month+"-"+day+"%20OR%20date:20??-"+month+"-"+day+"%29&sort=-/metadata/date"
  return today_URL

##################################################################################################

def iTunesPage():
  try:
    itunesURL = "http://" + Prefs['itunesIP'] + ":32400/music/iTunes/Artists"
    itunesArtistsPage = XML.ElementFromURL(itunesURL, errors='ignore')
  except:
    itunesArtistsPage = None
  return itunesArtistsPage