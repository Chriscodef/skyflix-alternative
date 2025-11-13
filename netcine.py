from urllib.parse import urlparse, quote_plus
import requests
from bs4 import BeautifulSoup
import re
import json
import base64

HOST_VOD = 'https://netcinez.si/'
# Additional sources to try (added per request)
HOSTS = [
    'https://netcinez.si/',
    'https://netcine.icu/',
    'https://www.anroll.net/',
    'https://redecanais.lc/',
    'https://animesdrive.blog/',
    'https://ultracine.org/',
    'https://megaflix.store/',
    'https://top-flix.yachts/',
    'https://top-flix.yachts/casa/'
]

def catalog_search(text):
    catalog = []
    url = 'https://v3.sg.media-imdb.com/suggestion/x/' + quote_plus(text) + '.json?includeVideos=1'
    try:
        data = requests.get(url).json()['d']
        for i in data:
            try:
                poster = i['i']['imageUrl']
                id = i['id']
                title = i['l']
                tp = i['qid']
                if 'series' in tp.lower():
                    tp = 'series'
                y = i['y']
                if 'tt' in id:
                    catalog.append({
                        "id": id,
                        "type": tp,
                        "title": title,
                        "year": int(y),
                        "poster": poster
                    })
            except:
                pass
    except:
        pass
    return catalog

def resolve_stream(url):
    parsed_url = urlparse(url)
    referer = '%s://%s/'%(parsed_url.scheme,parsed_url.netloc)        
    stream = ''
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/88.0.4324.96 Safari/537.36"}
    headers.update({'Cookie': 'XCRF%3DXCRF', 'Referer': referer})
    try:
        # find player
        r = requests.get(url,headers=headers)
        src = r.text
        soup = BeautifulSoup(src, 'html.parser')
        # common pattern: link inside #content
        try:
            url = soup.find('div', {'id': 'content'}).find_all('a')[0].get('href', '')
        except:
            # fallback: try iframe src or first anchor
            iframe = soup.find('iframe')
            if iframe and iframe.get('src'):
                url = iframe.get('src')
            else:
                a = soup.find('a', href=True)
                if a:
                    url = a.get('href', '')
    except:
        pass        
            
    try:
        r = requests.get(url,headers=headers)
        src = r.text
        regex_pattern = r'<source[^>]*\s+src="([^"]+)"'
        alto = []
        baixo = []
        matches = re.findall(regex_pattern, src)
        for match in matches:
            if 'ALTO' in match:
                alto.append(match)
            if 'alto' in match:
                alto.append(match)
            if 'BAIXO' in match:
                baixo.append(match)
            if 'baixo' in match:
                baixo.append(match)  
        if alto:
            stream = alto[-1]
            if ' ' in stream:
                stream = ''
            #stream = stream.replace(' ', '')
        elif baixo:
            stream = baixo[-1]
            if ' ' in stream:
                stream = ''            
            #stream = stream.replace(' ', '')        
    except:
        pass
    # fallbacks: try to find iframe src or video tags directly in the initial page
    if not stream:
        try:
            r2 = requests.get(url, headers=headers)
            s2 = r2.text
            soup2 = BeautifulSoup(s2, 'html.parser')
            # video tag
            video = soup2.find('video')
            if video and video.get('src'):
                stream = video.get('src')
            else:
                source = soup2.find('source')
                if source and source.get('src'):
                    stream = source.get('src')
                else:
                    iframe = soup2.find('iframe')
                    if iframe and iframe.get('src'):
                        stream = iframe.get('src')
            # try regex for common JS patterns
            if not stream:
                # match file: '...' or file: "..."
                m = re.findall(r"file\s*[:=]\s*['\"]([^'\"]+)['\"]", s2)
                if m:
                    stream = m[-1]
        except:
            pass
    return stream, headers

def search_term(imdb):
    url = 'https://www.imdb.com/pt/title/%s/'%imdb
    keys = []
    try:
        r = requests.get(url,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0', 'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3'})
        src = r.text
        script = re.findall('json">(.*?)</script>', src, re.DOTALL)[0]
        title = re.findall('<title>(.*?)</title>', src)[0]
        data = json.loads(script)
        name = data.get('name', '')
        name2 = data.get('alternateName', '')
        if name:
            keys.append(name)
        if name2:
            keys.append(name2)
        try:
            #year_ = re.findall('Série de TV (.*?)\)', title)
            year_ = re.findall(r'Série de TV (.*?)\)', title)
            if not year_:
                #year_ = re.findall('\((.*?)\)', title)
                year_ = re.findall(r'\((.*?)\)', title)
            if year_:
                year = year_[0]
                try:
                    year = year.split('–')[0]
                except:
                    pass
        except:
            year = ''       

    except:
        pass
    return keys, year

def opcoes_filmes(url,headers, host):
    dublado = []
    legendado = []         
    try:
        headers.update({'Cookie': 'XCRF%3DXCRF'})
        r = requests.get(url,headers=headers)
        src = r.text
        soup = BeautifulSoup(src,'html.parser')
        player = soup.find('div', {'id': 'player-container'})
        if player:
            botoes = player.find('ul', {'class': 'player-menu'})
            op = botoes.findAll('li') if botoes else []
        else:
            # fallback: try to find player-menu anywhere
            botoes = soup.find('ul', {'class': 'player-menu'})
            op = botoes.findAll('li') if botoes else []
        op_list = []
        if op:
            for i in op:
                a = i.find('a')
                id_ = a.get('href', '').replace('#', '')
                op_name = a.text
                try:
                    op_name = op_name.decode('utf-8')
                except:
                    pass
                op_name = op_name.replace(' 1', '').replace(' 2', '').replace(' 3', '').replace(' 4', '').replace(' 5', '')
                op_name = op_name.strip()
                op_name = op_name.upper()
                op_list.append((op_name,id_))
        if op_list:
            for name, id_ in op_list:
                # try to locate iframe by id inside player
                iframe = None
                try:
                    if player:
                        iframe = player.find('div', {'class': 'play-c'}).find('div', {'id': id_}).find('iframe')
                except:
                    iframe = None
                if not iframe:
                    # fallback: find iframe with id or last iframe
                    iframe = soup.find('iframe')
                iframe_src = iframe.get('src', '') if iframe else ''
                if iframe_src and not iframe_src.startswith('http') and host:
                    link = host.rstrip('/') + '/' + iframe_src.lstrip('/')
                else:
                    link = iframe_src
                if 'dublado' in name.lower() and not 'streamtape' in link:
                    dublado.append(link)                    
                if 'legendado' in name.lower() and not 'streamtape' in link:
                    legendado.append(link)
        else:
            # If no op_list found, try to get iframes directly and treat them as available streams
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src_if = iframe.get('src', '')
                if src_if and 'streamtape' not in src_if:
                    # unknown language, append to legendado as fallback
                    legendado.append(src_if)
    except:
        pass
    dub = ''
    leg = ''
    if dublado:
        dub = dublado[-1]
    if legendado:
        leg = legendado[-1]
    return dub, leg
    
def check_item(search,headers,year_imdb,text):
    r = requests.get(search,headers=headers)
    src = r.text
    soup = BeautifulSoup(src,'html.parser')
    box = soup.find("div", {"id": "box_movies"})
    movies = box.find_all("div", {"class": "movie"})
    count = 0
    for i in movies:
        try:
            year = i.find('span', {'class': 'year'}).text
            year = year.replace('–', '')
        except:
            year = ''
        name = i.find('h2').text
        try:
            name = name.decode('utf-8')
        except:
            pass
        try:
            name = name.decode()
        except:
            pass           
        if ':' in text:
            text_search = text.split(':')[1]
            text_search = text_search.replace(' ', '')
            text_search = text_search.lower()
            name_search = name.replace(' ', '')
            name_search = name_search.lower()
            if text_search in name_search:
                count += 1
                break
        else:
            if str(year_imdb) in str(year):
                count += 1
                break
            elif str(int(year_imdb) + 1) in str(year):
                count += 1         
                break
            elif str(int(year_imdb) - 1) in str(year):
                count += 1
                break
    if count > 0:
        return movies
    else:
        return []        
        



def scrape_search(host,headers,text,alternate,year_imdb,type):
    # fix search
    text = text.replace('&amp;', '&')
    alternate = alternate.replace('&amp;', '&')
    url = requests.get(host,headers=headers).url
    url_parsed = urlparse(url)
    new_host = url_parsed.scheme + '://' + url_parsed.hostname + '/'
    try:
        keys_search = text.split(' ')
        if len(keys_search) > 2:
            search_ = ' '.join(keys_search[:-1])
        else:
            search_ = text
    except:
        search_ = text
    try:
        search_count = len(search_.split(' '))
        if search_count > 2 and ':' in text:
            search_ = text.split(': ')[1]
    except:
        pass   
    url_search = new_host + '?s=' + quote_plus(search_)
    headers.update({'Cookie': 'XCRF%3DXCRF'})
    m1 = check_item(url_search,headers,year_imdb,text)
    if m1:
        movies = m1
    else:
        try:
            if ':' in text:
                param_search = text.split(':')[1]
                url_search2 = new_host + '?s=' + quote_plus(param_search)
                m2 = check_item(url_search2,headers,year_imdb,text)
                if m2:
                    movies = m2
                else:
                    movies = []
            else:
                movies = []
        except:
            movies = []
    for i in movies:
        name = i.find('h2').text
        try:
            name = name.decode('utf-8')
        except:
            pass
        name_backup = name
        text_backup = text
        textalternate_backup = alternate
        try:
            keys = name.split(' ')
            name2 = ' '.join(keys[:-1])
        except:
            name2 = ''
        try:
            keys2 = text.split(' ')
            text2 = ' '.join(keys2[:-1])
        except:
            text2 = ''                           
        try:
            year = i.find('span', {'class': 'year'}).text
            year = year.replace('–', '')
        except:
            year = ''
        try:
            text = text.lower()
            text = text.replace(':', '')
        except:
            pass
        try:
            textalternate = alternate.lower()
            textalternate = textalternate.replace(':', '')
        except:
            pass        
        try:
            name = name.lower()
            name = name.replace(':', '')
        except:
            pass
        try:
            text2 = text2.lower()
        except:
            pass
        try:
            name2 = name2.lower()
        except:
            pass
        try:
            name3 = name2.replace(' –', ':')
        except:
            name3 = ''
        try:
            count_text = len(name3.split(' '))
        except:
            count_text = 0
        try:
            if ':' in name_backup:
                name4 = name_backup.split(': ')[1]
                name4 = name4.lower()
            else:
                name4 = ''
        except:
            name4 = ''
        try:
            if ':' in text_backup:
                text3 = text_backup.split(': ')[1]
                text3 = text3.lower()
            else:
                text3 = ''
        except:
            text3 = ''
        try:
            if ':' in textalternate_backup:
                textalternate2 = textalternate_backup.split(': ')[1]
                textalternate2 = textalternate2.lower()
            else:
                textalternate2 = ''
        except:
            textalternate2 = ''            
        if '&' in text:
            text4 = text.replace('&', 'e')
        else:
            text4 = text
        if '&' in name and not '&amp;' in name:
            name5 = name.replace('&', 'e')
        else:
            name5 = name

        if ' e ' in text:
            text5 = text.replace(' e ', ' & ')
        else:
            text5 = text 
        if ' e ' in name:
            name6 = name.replace(' e ', ' & ')
        else:
            name6 = name
        try:
            count_text2 = len(text.split(' '))
        except:
            count_text2 = 0
        try:
            img = i.find('div', {'class': 'imagen'})
            link = img.find('a').get('href', '')
        except:
            link = ''
        # check count names:
        count_name_ = len(name)
        count_text_ = len(text)
        if type == 'tvshows' and '/tvshows/' in link:
            if text in name and str(year_imdb) in str(year) or text2 in name2 and str(year_imdb) in str(year):
                return link, new_host
            elif text2 in name3 and str(year_imdb) in str(year):
                return link, new_host 
            elif text2 in name3 and str(int(year_imdb) + 1) in str(year) and count_text > 1 and not count_name_ > count_text_:     
                return link, new_host
            elif text2 in name3 and str(int(year_imdb) - 1) in str(year) and count_text > 1 and not count_name_ > count_text_:    
                return link, new_host
            elif text3 in name4 and str(year_imdb) in str(year) and text3 and name4:
                return link, new_host
            elif text4 in name5 and str(year_imdb) in str(year) and text4 and name5:               
                return link, new_host
            elif len(text5) == len(name6) and str(year_imdb) in str(year) and text5 and name6:              
                return link, new_host
            elif textalternate in name and str(year_imdb) in str(year) or textalternate2 in name4 and str(year_imdb) in str(year):
                return link, new_host
            elif text in name and str(int(year_imdb) + 1) in str(year) and count_text2 > 0 and not count_name_ > count_text_:
                return link, new_host
            elif text in name and str(int(year_imdb) -1) in str(year) and count_text2 > 0 and not count_name_ > count_text_:
                return link, new_host              
        elif type == 'movies' and not '/tvshows/' in link: 
            if text in name and str(year_imdb) in str(year) or text2 in name2 and str(year_imdb) in str(year):
                return link, new_host
            elif text2 in name3 and str(year_imdb) in str(year):
                return link, new_host 
            elif text2 in name3 and str(int(year_imdb) + 1) in str(year) and count_text > 1 and not count_name_ > count_text_:     
                return link, new_host
            elif text2 in name3 and str(int(year_imdb) - 1) in str(year) and count_text > 1 and not count_name_ > count_text_:    
                return link, new_host
            elif text3 in name4 and str(year_imdb) in str(year) and text3 and name4:
                return link, new_host
            elif text4 in name5 and str(year_imdb) in str(year) and text4 and name5:               
                return link, new_host
            elif len(text5) == len(name6) and str(year_imdb) in str(year) and text5 and name6:              
                return link, new_host
            elif textalternate in name and str(year_imdb) in str(year) or textalternate2 in name4 and str(year_imdb) in str(year):
                return link, new_host
            elif text in name and str(int(year_imdb) + 1) in str(year) and count_text2 > 0 and not count_name_ > count_text_:
                return link, new_host
            elif text in name and str(int(year_imdb) -1) in str(year) and count_text2 > 0 and not count_name_ > count_text_:
                return link, new_host                                                            
    return '', ''   


def search_link(id, host=HOST_VOD):
    streams_final = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/88.0.4324.96 Safari/537.36"}
    try:
        if ':' in id:
            parts = id.split(':')
            imdb = parts[0]
            season = parts[1]
            episode = parts[2]
            search_text, year_imdb = search_term(imdb)
            if search_text and year_imdb:
                text = search_text[-1]
                alternate = search_text[0]
                link, new_host = scrape_search(host,headers,text,alternate,year_imdb,'tvshows')
                if '/tvshows/' in link:
                    #### SÉRIES EPISODES
                    r = requests.get(link,headers=headers)
                    src = r.text
                    soup = BeautifulSoup(src,'html.parser')
                    s = soup.find('div', {'id': 'movie'}).find('div', {'class': 'post'}).find('div', {'id': 'cssmenu'}).find('ul').find_all('li', {'class': 'has-sub'})
                    for n, i in enumerate(s):
                        n += 1
                        if int(season) == n:
                            e = i.find('ul').find_all('li')
                            for n, i in enumerate(e):
                                n += 1
                                if int(episode) == n:
                                    e_info = i.find('a')
                                    link = e_info.get('href')
                                    dub, leg = opcoes_filmes(link,headers, new_host)
                                    if dub:                                        
                                        stream_dub, headers_dub = resolve_stream(dub)
                                        if stream_dub:
                                            item_dub = {
                                                "url": stream_dub,
                                                "name": "SKYFLIX",
                                                "description": "NTC Server - Dublado",
                                                "behaviorHints": {
                                                "notWebReady": True,
                                                "proxyHeaders": {
                                                                "request": {
                                                                "User-Agent": headers_dub["User-Agent"],
                                                                "Referer": headers_dub["Referer"],
                                                                "Cookie": headers_dub["Cookie"]
                                                                }
                                                            }
                                                    }
                                            }
                                            streams_final.append(item_dub)
                                    if leg:                                        
                                        stream_leg, headers_leg = resolve_stream(leg)
                                        if stream_leg:
                                            item_leg = {
                                                "url": stream_leg,
                                                "name": "SKYFLIX",
                                                "description": "NTC Server - Legendado",
                                                "behaviorHints": {
                                                "notWebReady": True,
                                                "proxyHeaders": {
                                                                "request": {
                                                                "User-Agent": headers_leg["User-Agent"],
                                                                "Referer": headers_leg["Referer"],
                                                                "Cookie": headers_leg["Cookie"]
                                                                }
                                                            }
                                                    }
                                            }
                                            streams_final.append(item_leg)                                            
                                    break
                            break   
        else:
            imdb = id
            search_text, year_imdb = search_term(imdb)
            if search_text and year_imdb:
                text = search_text[-1]
                alternate = search_text[0]
                link, new_host = scrape_search(host,headers,text,alternate,year_imdb,'movies')
                if not '/tvshows/' in link:
                    dub, leg = opcoes_filmes(link,headers, new_host)
                    if dub:                                        
                        stream_dub, headers_dub = resolve_stream(dub)
                        if stream_dub:
                            item_dub = {
                                "url": stream_dub,
                                "name": "SKYFLIX",
                                "description": "NTC Server - Dublado",
                                "behaviorHints": {
                                "notWebReady": True,
                                "proxyHeaders": {
                                                "request": {
                                                "User-Agent": headers_dub["User-Agent"],
                                                "Referer": headers_dub["Referer"],
                                                "Cookie": headers_dub["Cookie"]
                                                }
                                            }
                                    }
                            }
                            streams_final.append(item_dub)
                    if leg:                                        
                        stream_leg, headers_leg = resolve_stream(leg)
                        if stream_leg:
                            item_leg = {
                                "url": stream_leg,
                                "name": "SKYFLIX",
                                "description": "NTC Server - Legendado",
                                "behaviorHints": {
                                "notWebReady": True,
                                "proxyHeaders": {
                                                "request": {
                                                "User-Agent": headers_leg["User-Agent"],
                                                "Referer": headers_leg["Referer"],
                                                "Cookie": headers_leg["Cookie"]
                                                }
                                            }
                                    }
                            }
                            streams_final.append(item_leg)  
    except:
        pass
    return streams_final


def url_para_base64(url):
    # Converte a URL para bytes e codifica em base64 URL-safe
    return base64.urlsafe_b64encode(url.encode()).decode()


def base64_para_url(base64_str):
    # Corrige padding se estiver faltando
    padding = '=' * (-len(base64_str) % 4)
    return base64.urlsafe_b64decode(base64_str + padding).decode()



def ntc_search_catalog(query, host=None):
    catalog = []
    query = query.replace('&amp;', '&')
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/88.0.4324.96 Safari/537.36"}
    # host override (keeps backward compatibility)
    use_host = host or HOST_VOD
    try:
        url = requests.get(use_host,headers=headers).url
        url_parsed = urlparse(url)
        new_host = url_parsed.scheme + '://' + url_parsed.hostname + '/'
    except:
        new_host = use_host
    url_search = new_host + '?s=' + quote_plus(query)
    try:
        r = requests.get(url_search,headers=headers)
        src = r.text
        soup = BeautifulSoup(src,'html.parser')
        box = soup.find("div", {"id": "box_movies"})
        movies = box.find_all("div", {"class": "movie"})
        for i in movies:
            try:
                year = i.find('span', {'class': 'year'}).text
                year = year.replace('–', '')
            except:
                year = 0
            name = i.find('h2').text
            try:
                name = name.decode('utf-8')
            except:
                pass
            try:
                name = name.decode()
            except:
                pass
            try:
                image = i.find('img').get('src', '')
            except:
                image = ''
            if image:
                image = 'https://da5f663b4690-proxyimage.baby-beamup.club/proxy-image/?url=' + image
            title = name
            try:
                img = i.find('div', {'class': 'imagen'})
                link = img.find('a').get('href', '')
            except:
                link = ''
            if link and year:
                if '/tvshows/' in link:
                    tp = 'series'
                else:
                    tp = 'movie'
                id_ = 'skyflix:' + url_para_base64(link).replace('=', '')
                try:
                    catalog.append({
                        "id": id_,
                        "type": tp,
                        "title": title,
                        "year": int(year),
                        "poster": image
                    }) 
                except:
                    pass
    except:
        pass
    return catalog


def meta_ntc(type, id):
    meta = {}
    if not 'skyflix' in id:
        return meta
    id_ = id.replace('skyflix:', '')
    id_ = base64_para_url(id_)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/88.0.4324.96 Safari/537.36"}
        r = requests.get(id_,headers=headers)
        src = r.text
        soup = BeautifulSoup(src,'html.parser')
        if type == 'movie':
            info = soup.find('div', {'id': 'movie'}).find('div', {'class': 'post'})
            try:
                image = info.find('div', {'class': 'lazyload cover'}).get('data-bg', '')
                if image:
                    image = 'https://da5f663b4690-proxyimage.baby-beamup.club/proxy-image/?url=' + image
            except:
                image = ''               
            name = info.find('div', {'class': 'dataplus'}).find('h1').text.strip().replace('\n', '').replace('\r', '')
            try:
                year = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find_all('span')[1].find('a').text.strip().replace('\n', '').replace('\r', '')
                year = int(year)
            except:
                year = 0
            try:
                imdb_rating = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find('div', {'class': 'rank'}).text.strip().replace('\n', '').replace('\r', '')
                if imdb_rating == '0':
                    imdb_rating = 0.0
                else:
                    imdb_rating = float(imdb_rating)
            except:
                imdb_rating = 0.0 
            genres = []  
            try:       
                genres_a = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find_all('a', {'rel': 'category tag'})
                if genres_a:                    
                    for i in genres_a:
                        genre_name = i.text
                        if not 'atuali' in genre_name.lower():
                            genres.append(genre_name)
            except:
                pass
            try:
                runtime = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find_all('span')[2].text.strip().replace('Min', 'min')
            except:
                runtime = ''
            try:
                description = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-2'}).find('p').text.strip()
            except:
                description = ''
            meta = {'id': id, 
                    'type': 'movie', 
                    'name': name, 
                    'year': year,
                    'runtime': runtime,
                    'imdbRating': imdb_rating,
                    'poster': image,
                    'background': image,
                    'genres': genres,
                    'trailers': [],
                    'description': description,
                    'behaviorHints': {'defaultVideoId': id,
                        'hasScheduledVideos': False}
            }
        elif type == 'series':
            info = soup.find('div', {'id': 'movie'}).find('div', {'class': 'post'})
            try:
                image = info.find('div', {'class': 'lazyload cover'}).get('data-bg', '')
                if image:
                    image = 'https://da5f663b4690-proxyimage.baby-beamup.club/proxy-image/?url=' + image
            except:
                image = ''               
            name = info.find('div', {'class': 'dataplus'}).find('h1').text.strip().replace('\n', '').replace('\r', '')
            try:
                year = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find_all('span')[1].find('a').text.strip().replace('\n', '').replace('\r', '')
                year = int(year)
            except:
                year = 0
            try:
                imdb_rating = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find('div', {'class': 'rank'}).text.strip().replace('\n', '').replace('\r', '')
                if imdb_rating == '0':
                    imdb_rating = 0.0
                else:
                    imdb_rating = float(imdb_rating)
            except:
                imdb_rating = 0.0 
            genres = []  
            try:       
                genres_a = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find_all('a', {'rel': 'category tag'})
                if genres_a:                    
                    for i in genres_a:
                        genre_name = i.text
                        if not 'atuali' in genre_name.lower():
                            genres.append(genre_name)
            except:
                pass
            try:
                runtime = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-1'}).find_all('span')[2].text.strip().replace('Min', 'min')
            except:
                runtime = ''
            try:
                description = info.find('div', {'class': 'dataplus'}).find('div', {'id': 'dato-2'}).find('p').text.strip()
            except:
                description = ''
            videos = []
            s = soup.find('div', {'id': 'movie'}).find('div', {'class': 'post'}).find('div', {'id': 'cssmenu'}).find('ul').find_all('li', {'class': 'has-sub'})
            for season, i in enumerate(s):
                season_number = season + 1
                e = i.find('ul').find_all('li')
                for episode, i in enumerate(e):
                    episode_number = episode + 1
                    try:
                        title_ep = i.find_all('span')[1].text.strip()
                    except:
                        title_ep = f'Episódio {str(episode_number)}'
                    ep_meta = {
                    'id': id + ':' + str(season_number) + ':' + str(episode_number), 
                    'season': int(season_number), 
                    'number': int(episode_number), 
                    'episode': int(episode_number), 
                    'name': title_ep, 
                    'thumbnail': image
                            }
                    videos.append(ep_meta)                

            meta = {'id': id, 
                    'type': 'series', 
                    'name': name, 
                    'year': year,
                    'imdbRating': imdb_rating,
                    'poster': image,
                    'background': image,
                    'genres': genres,
                    'trailers': [],
                    'description': description,
                    'videos': videos,
                    'behaviorHints': {'hasScheduledVideos': False}
            }               
    except:
        pass
    return meta

def get_stream_ntc(type, id):
    streams_final = []
    if not 'skyflix' in id:
        return streams_final
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/88.0.4324.96 Safari/537.36"}
    # default host for this call
    new_host = HOST_VOD
    try:
        url = requests.get(HOST_VOD,headers=headers).url
        url_parsed = urlparse(url)
        new_host = url_parsed.scheme + '://' + url_parsed.hostname + '/'
    except:
        new_host = HOST_VOD
    if type == 'movie':
        id_ = id.replace('skyflix:', '')
        id_ = base64_para_url(id_)
        link = id_
        if not '/tvshows/' in link:
            dub, leg = opcoes_filmes(link,headers, new_host)
            if dub:                                        
                stream_dub, headers_dub = resolve_stream(dub)
                if stream_dub:
                    item_dub = {
                        "url": stream_dub,
                        "name": "SKYFLIX",
                        "description": "NTC Server - Dublado",
                        "behaviorHints": {
                        "notWebReady": True,
                        "proxyHeaders": {
                                        "request": {
                                        "User-Agent": headers_dub["User-Agent"],
                                        "Referer": headers_dub["Referer"],
                                        "Cookie": headers_dub["Cookie"]
                                        }
                                    }
                            }
                    }
                    streams_final.append(item_dub)
            if leg:                                        
                stream_leg, headers_leg = resolve_stream(leg)
                if stream_leg:
                    item_leg = {
                        "url": stream_leg,
                        "name": "SKYFLIX",
                        "description": "NTC Server - Legendado",
                        "behaviorHints": {
                        "notWebReady": True,
                        "proxyHeaders": {
                                        "request": {
                                        "User-Agent": headers_leg["User-Agent"],
                                        "Referer": headers_leg["Referer"],
                                        "Cookie": headers_leg["Cookie"]
                                        }
                                    }
                            }
                    }
                    streams_final.append(item_leg)
    elif type == 'series':
        id_ = id.replace('skyflix:', '')
        parts = id_.split(':')
        link = base64_para_url(parts[0])
        season = parts[1]
        episode = parts[2]
        try:
            r = requests.get(link,headers=headers)
            src = r.text
            soup = BeautifulSoup(src,'html.parser')
            s = soup.find('div', {'id': 'movie'}).find('div', {'class': 'post'}).find('div', {'id': 'cssmenu'}).find('ul').find_all('li', {'class': 'has-sub'})
            for n, i in enumerate(s):
                n += 1
                if int(season) == n:
                    e = i.find('ul').find_all('li')
                    for n, i in enumerate(e):
                        n += 1
                        if int(episode) == n:
                            e_info = i.find('a')
                            link = e_info.get('href')
                            dub, leg = opcoes_filmes(link,headers, new_host)
                            if dub:                                        
                                stream_dub, headers_dub = resolve_stream(dub)
                                if stream_dub:
                                    item_dub = {
                                        "url": stream_dub,
                                        "name": "SKYFLIX",
                                        "description": "NTC Server - Dublado",
                                        "behaviorHints": {
                                        "notWebReady": True,
                                        "proxyHeaders": {
                                                        "request": {
                                                        "User-Agent": headers_dub["User-Agent"],
                                                        "Referer": headers_dub["Referer"],
                                                        "Cookie": headers_dub["Cookie"]
                                                        }
                                                    }
                                            }
                                    }
                                    streams_final.append(item_dub)
                            if leg:                                        
                                stream_leg, headers_leg = resolve_stream(leg)
                                if stream_leg:
                                    item_leg = {
                                        "url": stream_leg,
                                        "name": "SKYFLIX",
                                        "description": "NTC Server - Legendado",
                                        "behaviorHints": {
                                        "notWebReady": True,
                                        "proxyHeaders": {
                                                        "request": {
                                                        "User-Agent": headers_leg["User-Agent"],
                                                        "Referer": headers_leg["Referer"],
                                                        "Cookie": headers_leg["Cookie"]
                                                        }
                                                    }
                                            }
                                    }
                                    streams_final.append(item_leg)                                            
                            break
                    break
        except:
            pass
    return streams_final



def search_link_multi(id):
    """Try search_link across configured HOSTS. Returns combined streams list."""
    streams = []
    seen_urls = set()
    for h in HOSTS:
        try:
            # call the original search_link implementation to avoid recursion
            s = _orig_search_link(id, host=h) if '_orig_search_link' in globals() else search_link(id, host=h)
            for item in s:
                url = item.get('url')
                if url and url not in seen_urls:
                    streams.append(item)
                    seen_urls.add(url)
        except:
            continue
    return streams


def ntc_search_catalog_multi(query):
    """Aggregate catalog results from all HOSTS (de-duplicated by id)."""
    catalog = []
    seen = set()
    for h in HOSTS:
        try:
            # call original catalog search to avoid recursion
            items = _orig_ntc_search_catalog(query, host=h) if '_orig_ntc_search_catalog' in globals() else ntc_search_catalog(query, host=h)
            for it in items:
                id_ = it.get('id')
                if id_ and id_ not in seen:
                    catalog.append(it)
                    seen.add(id_)
        except:
            continue
    return catalog


def get_stream_multi(type, id):
    """Wrapper that currently delegates to get_stream_ntc (keeps API stable)."""
    # As ids include full links base64 encoded, the original get_stream_ntc can resolve them.
    return _orig_get_stream_ntc(type, id) if '_orig_get_stream_ntc' in globals() else get_stream_ntc(type, id)


# --- Preserve originals and expose aggregated defaults ---
# Keep references to original implementations so we can fall back if needed
_orig_search_link = search_link
_orig_ntc_search_catalog = ntc_search_catalog
_orig_get_stream_ntc = get_stream_ntc


def _search_link_aggregated(id):
    """Default search_link: try across all HOSTS and aggregate streams."""
    return search_link_multi(id)


def _ntc_search_catalog_aggregated(query):
    """Default catalog search: aggregate results from all HOSTS."""
    return ntc_search_catalog_multi(query)


def _get_stream_aggregated(type, id):
    """Default get_stream: try the original resolver (IDs are per-link).
    If the id is an imdb-style id, attempt aggregated search_link_multi to gather streams from all hosts."""
    # If id is a skyflix encoded link, keep original behavior
    if isinstance(id, str) and id.startswith('skyflix:'):
        return _orig_get_stream_ntc(type, id)
    # otherwise attempt aggregated search by imdb id
    try:
        streams = search_link_multi(id)
        return streams
    except:
        return _orig_get_stream_ntc(type, id)


# Reassign public names to aggregated versions (keeps compatibility)
search_link = _search_link_aggregated
ntc_search_catalog = _ntc_search_catalog_aggregated
get_stream_ntc = _get_stream_aggregated

        


