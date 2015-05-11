
# Generating sitemap.xml
# 1) Add URLs to sitemap only from <a></a> html tags 
# 2) Add URLs to sitemap even if errors occurs on its load&read
# 3) URLs that contains '#' places to sitemap without part of URL after '#'
# 4) Consider that http://www.example.com != http://example.com
# 5) Consider that mainpage = 0 level page (so MAX_LEVEL = 2)
# 6) Consider that relative /components != /components.html
# 7) Display notifications when sitemap.xml file more than 50,000 lines or 10 Mb
# 8) Do not try to load&read URLs on last level pages


import queue
import threading
import os.path
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup as bs


MAX_THREADS = 20
MAX_PAGE_LEVEL = 2
BASEDIR = os.path.abspath(os.path.dirname(__file__))


class ThreadUrl(threading.Thread): 
    """Class for fetching URLs using threads

    Arguments:
    input_q --  queue.Queue() instance with URL for parsing
    output_q -- queue.Queue() instance for results :)
    """

    def __init__(self, input_q, output_q):
        threading.Thread.__init__(self)
        self.input_q = input_q
        self.output_q = output_q

    def run(self):
        while True:
            # grabs url from queue
            level, u = self.input_q.get()

            main = '{0.scheme}://{0.netloc}/'.format(urlsplit(u))

            # fetching urls
            if level < MAX_URL_LEVEL:
                html = _get_content(u)
                if not isinstance(html, list):
                    soup = bs(html)
                    for link in soup.find_all('a'):
                        href = link.get('href')
                        
                        if not href or len(href) < 2:
                            continue

                        # Check if URL is relative
                        elif not urlsplit(href)[0] and not urlsplit(href)[1]:
                            self.output_q.put((level+1, _url_discard(urljoin(u, href))))
                        
                        elif href.startswith(main):
                            self.output_q.put((level+1, _url_discard(href)))
                else:
                    # Place for possible error logs (:
                    pass

            # signals to queue job is done
            self.input_q.task_done()


def _url_discard(url):
    # Drop part of URL after '#' symbol
    url =  url[:url.index('#')] if '#' in url else url
    
    # Shit happens sometimes..
    while '/../' in url or '/./' in url:
        url = url.replace('/../', '/').replace('/./', '/')
    return url

def _symbol_escaping(url):
    escaping = [('&', '&amp;'), ('\'', '&apos;'), ('\"', '&quot;'), ('>', '&gt;'), ('<', '&lt;')]
    for s in escaping:
        url = url.replace(s[0], s[1])
    return url

def _make_xml(url_list):
    filename = 'sitemap_{0}.xml'.format(urlsplit(url_list[0])[1].replace('.', '_'))
    path = os.path.join(BASEDIR, 'static', filename)

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in url_list:
        sitemap += '  <url>\n    <loc>{}<loc>\n  </url>\n'.format(_symbol_escaping(url))
    sitemap += "</urlset>"

    with open(path, 'wb') as f:
        f.write(sitemap.encode('utf-8'))

    return filename

def _get_content(url):
    # return html content from given url or list of errors
    errors = []
    req = Request(url)
    try:
        response = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):
            errors.append('We failed to reach a server. | Reason: {0} | URL: {1}'.format(e.reason, url))
        elif hasattr(e, 'code'):
            errors.append('The server couldn\'t fulfill the request. | Error code: {0} | URL: {1}'.format(e.code, url))
        else:
            errors.append('THIS IS ERROR! | {0} | URL: {1}'.format(str(e), url))
    else:
        # Don't parse content with conent-type != text/html
        if response.headers.get_content_type() == 'text/html':
            encoding = response.headers.get_content_charset()
            return response.read().decode(encoding if encoding else 'utf-8')
    return errors

def get_sitemap(url):
    """
    Generate sitemap.xml, starting from main page given by url
    """

    # Start from main page
    url = '{0.scheme}://{0.netloc}'.format(urlsplit(url))

    # Return list of errors if its occurs during load$open URL given by user
    tmp_result = _get_content(url)
    if isinstance(tmp_result, list):
        return tmp_result 
    else:
        # Handling redirects from main page
        url = urlopen(url).geturl()

    urls = {(0, url)}
    sitemap = {url}
    result = []

    # Parse URLs on each page level
    for _ in range(MAX_PAGE_LEVEL):
        
        input_q = queue.Queue()
        output_q = queue.Queue()
        
        # spawn a pool of threads, and pass them queue instance
        for i in range(min(MAX_THREADS, len(urls))):
            t = ThreadUrl(input_q, output_q)
            t.setDaemon(True)
            t.start()

        while urls:
            input_q.put(urls.pop())

        input_q.join()

        # Fill sitemap with unique URLs, fill urls with unique URLs that haven't yet visited
        tmp = set(output_q.queue)
        urls = {(x, y) for x, y in tmp if y not in sitemap}
        sitemap |= {y for x, y in tmp}

    # Delete duplicates like http://www.example.com/lol and http://www.example.com/lol/ from sitemap
    for url in sitemap:
        if not url.endswith('/') and url+'/' in sitemap:
            continue
        result.append(url)

    xml = _make_xml(sorted(result, key=lambda x: len(x)))
    return (xml, len(result), os.path.getsize(os.path.join(BASEDIR, 'static', xml)))


if __name__ == '__main__':
    get_sitemap('http://python.org/')



    