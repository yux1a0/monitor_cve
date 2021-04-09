# encoding=utf-8
import json
import requests
import datetime, time
import sqlite3
import logging

logging.basicConfig(filename='history.log', level='INFO', format='【%(asctime)s】%(levelname)s - %(message)s')

def telegram(msg):
    # 替换为自己的bot_id
    url = "https://api.telegram.org/xxxxx/sendMessage"
    requests.post(url,
                  data={
                      "chat_id": 12345678, # 替换为自己的chat_id
                      "text": f"【新的CVE相关仓库】\n{msg}"
                  })


def get_news():
    cnt = 0
    year = datetime.datetime.now().year
    while True:
        try:
            api_url = f"https://api.github.com/search/repositories?q=CVE-{year}&sort=updated"
            r = requests.get(api_url)
            if r.status_code == 200:
                data = json.loads(r.text)
            total = data['total_count']
            logging.info(f"监控CVE中，现有{total}个仓库...")
            if total <= cnt:
                continue
            page_size = 30
            page = 0
            pages = total // page_size + 1
            for page in range(1, pages + 1):
                api_url = f"https://api.github.com/search/repositories?q=CVE-{year}&sort=updated&per_page={page_size}&page={page}"
                r = requests.get(api_url)
                if r.status_code == 200:
                    data = json.loads(r.text)
                items = data['items']
                conn = sqlite3.connect('db.sqlite')
                cu = conn.cursor()
                cu.execute(
                    "CREATE TABLE IF NOT EXISTS cve_repositories(id integer primary key, r_id integer, name varchar(200), url varchar(200), desc text, author varchar(50));"
                )
                conn.commit()
                for item in items:
                    r_id = item['id']
                    name = item['name']
                    url = item['html_url']
                    desc = item['description'] if item['description'] else ''
                    author = item['owner']['login']

                    cu.execute("select * from cve_repositories where r_id = ?",
                            (r_id, ))
                    r = cu.fetchone()
                    if not r:
                        cu.execute(
                            f'INSERT INTO cve_repositories (r_id, name, url, desc, author) VALUES (?, ?, ?, ?, ?);',
                            (r_id, name, url, desc, author))
                        msg = json.dumps(
                            {
                                "r_id": r_id,
                                "name": name,
                                "url": url,
                                "desc": desc,
                                "author": author
                            },
                            indent=2)
                        telegram(msg)
                conn.commit()
                cu.close()
                conn.close()
            time.sleep(300)
        except Exception as e:
            logging.error(e)
        cnt = total

if __name__ == "__main__":
    get_news()
