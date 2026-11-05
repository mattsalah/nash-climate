import csv
import html
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# Scrapes the LobbyMap league table (https://lobbymap.org/LobbyMapScores) plus the
# headquarters listed on each organization's profile page. Takes ~40 minutes because the
# profile pages are slow, so the result is saved to input/lobbymap/lobbymap_scores.csv

output_filename = 'input/lobbymap/lobbymap_scores.csv'
TABLE_URL = 'https://lobbymap.org/evoke/1210721/fill_leaguetable'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')


###### LEAGUE TABLE #######

# Each row carries the score, engagement intensity, region and sector as data attributes
table = fetch(TABLE_URL)
rows = []
for m in re.finditer(r'<tr (data-area="[^"]*"[^>]*)>(.*?)</tr>', table, re.S):
    attrs = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(1)))
    tds = re.findall(r'<td[^>]*>(.*?)</td>', m.group(2), re.S)
    link = re.search(r'href="([^"]+)"', m.group(2))
    rows.append({
        'area': attrs.get('area'),  # company or influencer (industry association)
        'name': html.unescape(attrs.get('name', '')),
        'band': re.sub('<[^>]+>', '', tds[0]).strip() if tds else '',
        'score': attrs.get('score'),
        'engagement': attrs.get('engagement'),
        'region': html.unescape(attrs.get('region', '')),
        'sector': html.unescape(attrs.get('sector', '')),
        'uid': attrs.get('uid'),
        'url': link.group(1) if link else '',
    })
print(f"{len(rows)} organizations in league table")

###### HEADQUARTERS #######

def get_headquarters(row):
    for attempt in range(3):
        try:
            page = re.sub(r'<script.*?</script>|<style.*?</style>', '', fetch(row['url']), flags=re.S)
            text = [x.strip() for x in re.sub('<[^>]+>', '\n', page).split('\n') if x.strip()]
            time.sleep(0.3)
            return html.unescape(text[text.index('Headquarters') + 1]) if 'Headquarters' in text else ''
        except Exception:
            time.sleep(2 * (attempt + 1))
    return 'ERROR'


with ThreadPoolExecutor(4) as ex:
    hqs = list(ex.map(get_headquarters, rows))
for row, hq in zip(rows, hqs):
    row['headquarters'] = hq
print(f"{sum(h == 'ERROR' for h in hqs)} errors, {sum(h == '' for h in hqs)} blank headquarters")

###### SAVE ################

with open(output_filename, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
