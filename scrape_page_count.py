import requests
from bs4 import BeautifulSoup
import sys
import re
import sqlite3 as lite

SQLITE_DB = 'offers.db'


def get_pages(isbn):
    url = "https://www.google.com/search?q="+isbn+"+amazon&rlz=1C5CHFA_enUS763US768&oq="+isbn+"+amazon&aqs=chrome..69i57j69i60l3.596j0j1&sourceid=chrome&ie=UTF-8"
    # headers = {
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    #     "Accept-Encoding": "gzip, deflate, sdch, br",
    #     "Accept-Language": "en-US,en;q=0.8",
    #     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    # }
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    }

    r = requests.get(url, headers = headers)
    soup = BeautifulSoup(r.content, "html.parser")
    div = soup.find('div', {"id":'search'})
    result_links = div.find_all("a")
    p = re.compile("<li><b>(.*):</b> (.*) pages</li>")
    book_pages = 0
    for link in result_links:
        newurl = link.get("href")
        if newurl and newurl.startswith("https://www.amazon.com"):
            # print(newurl)
            ra = requests.get(newurl, headers = headers)
            soupa = BeautifulSoup(ra.content, "html.parser")
            matches = p.search(str(soupa))
            try:
                book_pages = int(matches.group(2))
                break
            except:
                pass
    return book_pages


def db_connect():
    con = None
    try:
        con = lite.connect(SQLITE_DB, check_same_thread=False)
    except lite.Error as e:
        if con:
            con.rollback()
        print("Connection error: {0}".format(e))
        sys.exit(1)

    return con


def db_query(con, sql, params=None):
    if not con:
        print("Not connected to the database")
        return None

    rows = None
    try:
        con.row_factory = lite.Row
        cur = con.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        rows = cur.fetchall()
    except lite.Error as e:
        print("Connection error: {0}".format(e))

    return rows


def get_success_transactions(con):
    isbns = {}
    sql = '''
            SELECT isbn, bookName
            FROM buyers_history B, textbooks T
            WHERE B.book_id=T.uuid AND success=1
            UNION ALL
            SELECT isbn, bookName
            FROM sellers_history S, textbooks T
            WHERE S.book_id=T.uuid AND success=1
            '''
    rows = db_query(con, sql)
    for item in rows:
        isbn = item[0].replace("-", "")
        if isbn not in isbns:
            isbns[isbn] = 0
        isbns[isbn] += 1
    return isbns


def main():
    con = db_connect()
    if not con:
        return
    isbns = get_success_transactions(con)
    total = 0
    for isbn, times in isbns.items():
        total += get_pages(isbn)*times
    print("Saved " + str(total) + " pages!")
    return total


if __name__ == "__main__":
    main()
