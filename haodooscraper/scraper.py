# For scrape Haodoo (http://www.haodoo.net)
# -*- coding: utf-8 -*-

from multiprocessing import Pool
from datetime import datetime
import re
import requests
import lxml.html
from haodooscraper.model import Page, Volume, session
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse
from urllib.parse import urlencode
import traceback

# DownloadPdb('A435')
ONCLICK_PATTERN = re.compile(
    "(?P<quote>[\"'])(?P<_id>[^(?P=quote)]*)(?P=quote)")
SET_TITLE_PATTERN = re.compile(
    "SetTitle\((?P<quote>[\"'])(?P<title>[^(?P=quote)]*)(?P=quote)\)")
base_url = 'http://www.haodoo.net/'


def scrape(url):
    r = requests.get(url)
    r.encoding = "big5"
    return r.text


def save_bookpages(book_dict):
    """
    book_dict is a dict, contain these keys: id, url, title.
    """
    if Page.is_existed(book_dict['id']):
        return
    book = Page.create(book_dict)
    session.add(book)
    session.commit()


def save_volume(volume_dict):
    """
    volume_dict is a dict, contain the keys: id, author, title, bookid, exts.
    exts is a list contain dicts.  The element contain these keys:
    volumeid, type, link.
    """
    if Volume.is_existed(volume_dict['id']):
        return

    volume = Volume.create(volume_dict)
    session.add(volume)
    session.commit()


def parse_books_from_html(html):
    """
    Parse the url of each book from the book list page.
    The book's title and url will be stored in database.
    """
    root = lxml.html.fromstring(html)
    for a in root.cssselect("a"):
        if not 'href' in a.attrib:
            continue
        href = a.attrib['href']
        if href.startswith("javascript"):
            continue
        if not href.startswith("http"):
            href = urljoin(base_url, href)
        book_title = a.text_content()

        d = parse_qs(urlparse(href).query)
        if 'M' in d and d['M'][0] in ('book', 'Share'):
            if 'P' in d:
                book_id = d['P'][0]
                book = {'id': book_id,
                        'url': href,
                        'title': book_title}
                save_bookpages(book)


def find_volume_id(onclick):
    """
    Find book id from the given string.  The string actually is javascript
    function.
    """
    # find which kind of quote, ' or "
    quote = "'"
    start = onclick.find(quote)
    if start == -1:
        quote = '"'

    _id = ''
    start = onclick.find(quote)
    end = onclick.rfind(quote)
    if start != -1 and end != -1:
        _id = onclick[start+1:end]

    return _id


def find_volume_id_2(onclick):
    """
    Find book id from the given string.  The string actually is javascript
    function.
    Regular expression version is slower than string find.
    """
    m = ONCLICK_PATTERN.search(onclick)
    if not m:
        return ""

    if m.group("_id"):
        return m.group("_id")

    return ""


def convert_to_dl_url(_id, ext):
    """
    According book_id and book type to generate download url.
    """
    result = list(urlparse(base_url))
    result[4] = urlencode({
        "M": "d",
        "P": "{0}.{1}".format(_id, ext)})
    return urlunparse(result)


def extract_set_title(html):
    start_pos = html.find('SetTitle("')
    if start_pos == -1:
        return ("", "")

    start_quote = html.find('"', start_pos)
    if start_quote == -1:
        return ("", "")

    end_quote = html.find('"', start_quote+1)
    if end_quote == -1:
        return ("", "")

    set_title = html[start_quote+1: end_quote-1]
    set_title = set_title.replace('《', ',')
    r = set_title.split(',')
    if len(r) != 2:
        return ("", "")
    return r


def extract_set_title_2(html):
    m = SET_TITLE_PATTERN.search(html)
    author = ""
    title = ""
    if not m:
        return (author, title)

    if m.group("title"):
        title = m.group("title")
        title = title.replace(
            '【', ',').replace(
                '《', ',').replace(
                    '】', '').replace(
                        '》', '')
        r = title.split(',')
        if len(r) > 1:
            author = r[0]
            title = r[1]

    return (author, title)


def analysis_book_html_and_save(book, html):
    doc = lxml.html.fromstring(html)
    volume_author, volume_name = extract_set_title_2(html)

    pdb_download_elements = doc.xpath('//a[contains(@href, "pdb")]')
    if len(pdb_download_elements):
        # old style page, only readonline and download link.
        save_item = pdb_download_elements[0]
        save_item_previous = save_item.getprevious()
        title = save_item_previous.text
        author = None
        if save_item_previous.getprevious() is not None:
            author = save_item_previous.getprevious().text
        volume = {
            'id': book.id,
            'bookid': book.id,
        }
        if title:
            volume['title'] = title
        else:
            volume['title'] = volume_name
        if author:
            volume['author'] = author
        else:
            volume['author'] = volume_author

        volume['exts'] = [{"volumeid": book.id,
                           "type": "pdb",
                           "link": urljoin(base_url,
                                           save_item.attrib['href'])}]
        return [volume]
    else:
        volumes = []
        volume = None
        exts = []
        for save_item in doc.xpath('//input[contains(@type, "button")]'):
            onclick = save_item.get('onclick')
            _id = find_volume_id_2(onclick)
            if "ReadOnline" in onclick or "ReadPdbOnline" in onclick:
                if volume is not None:
                    volume['exts'] = exts
                    volumes.append(volume)
                volume = {
                    'id': _id,
                    'author': save_item.getprevious().text,
                    'title': save_item.getprevious().tail,
                    'bookid': book.id,
                }
                exts = []
            elif "DownloadEpub" in onclick:
                dl_link = convert_to_dl_url(_id, "epub")
                exts.append({"volumeid": _id, "type": "epub", "link": dl_link})
            elif "DownloadUpdb" in onclick:
                dl_link = convert_to_dl_url(_id, "updb")
                exts.append({"volumeid": _id, "type": "updb", "link": dl_link})
            elif "DownloadPdb" in onclick:
                dl_link = convert_to_dl_url(_id, "pdb")
                exts.append({"volumeid": _id, "type": "pdb", "link": dl_link})
        if volume:
            volume['exts'] = exts
            volumes.append(volume)
        return volumes


def urls():
    params = [
        {"M": "hhd", "P": "home"},
        {"M": "guru", "P": "home"},
        {"M": "ting", "P": "1"},
        {"M": "yulin", "P": "home"},
        {"M": "fay-mon", "P": "home"},
        {"M": "anna", "P": "home"},
        {"M": "hwarong", "P": "1"},
        {"M": "foch", "P": "home"},
        {"M": "long", "P": "home"},
        {"M": "kuan", "P": "1"},
        {"M": "ken", "P": "home"},
        {"M": "marina", "P": "home"},

        {"M": "hd", "P": "100"},
        {"M": "hd", "P": "wisdom"},
        {"M": "hd", "P": "history"},
        {"M": "hd", "P": "martial"},
        {"M": "hd", "P": "mystery"},
        {"M": "hd", "P": "romance"},
        {"M": "hd", "P": "scifi"},
        {"M": "hd", "P": "fiction"},
    ]

    pr = list(urlparse(base_url))
    for param in params:
        pr[4] = urlencode(param)
        yield urlunparse(pr)


def get_suburl(url, page):
    """
    There are sub pages in every category, need to append '-1', '-2' in P.
    So http://www.haodoo.net/?M=hd&P=martial will be
    http://www.haodoo.net/?M=hd&P=martial-1
    """
    pr = list(urlparse(url))
    param = parse_qs(pr[4])
    for k, v in list(param.items()):
        param[k] = v[0]
    param["P"] = "{0}-{1}".format(param["P"], page)
    pr[4] = urlencode(param)
    return urlunparse(pr)


def grab_and_analysis(book):
    # grab html
    html = scrape(book.url)

    # analysis and store information into book
    return analysis_book_html_and_save(book, html)


def scrape_haodoo():
    """
    Main
    """
    skip_stage1 = False
    try:
        print(">>> Stage 1 - Collecting all book urls {}<<<".format(
            datetime.now()))
        if not skip_stage1:
            for url in urls():
                # print(url)
                html = scrape(url)
                parse_books_from_html(html)

                page = 1
                while True:
                    suburl = get_suburl(url, page)
                    #print(suburl)
                    if html.find(urlparse(suburl).query):
                        html = scrape(suburl)
                        if html.find("<strong>404") != -1:
                            break
                        parse_books_from_html(html)
                        page = page + 1
                    else:
                        break

        print(">>> Stage 2 - Analysising all book urls {}<<<".format(
            datetime.now()))
        p = Pool()
        results = p.map(grab_and_analysis, Page.query_all())
        # results = map(grab_and_analysis, Page.query_all())

        print(">>> Stage 3 - Saving results {}<<<".format(
            datetime.now()))
        for volumes in results:
            for volume in volumes:
                save_volume(volume)

        print(">>> State 4 - done {}<<<".format(datetime.now()))

    except Exception as e:
        print("Got exception:")
        print(e)
        print(traceback.format_exc())

if __name__ == "__main__":
    scrape_haodoo()
