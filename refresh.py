"""Fetch public upstream data, build in isolation, and promote only valid output."""
import csv, hashlib, html, io, json, os, pathlib, shutil, subprocess, sys, tempfile, time, urllib.request, zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
ROOT = pathlib.Path(__file__).resolve().parent
FOLDER = '1WI1UGcwgFKXJdqe08WI5sQTxRSI-ok33'
class FolderParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.files = {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); title = a.get('data-tooltip', ''); ident = a.get('data-id')
        if ident and title.startswith('DATABASE PURATA HARGA'):
            for suffix, kind in [(' Microsoft Excel','xlsx'), (' Google Sheets','sheet')]:
                if title.endswith(suffix):
                    self.files[ident] = {'id': ident, 'name':title[:-len(suffix)], 'kind':kind}
def fetch(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Malaysia-CPI-Dashboard/1.0'})
            with urllib.request.urlopen(req, timeout=120) as r: return r.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(2 ** attempt)
def validate_csv(raw, required):
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if not rows or not required.issubset(rows[0]): raise ValueError('Unexpected DOSM CSV schema')
    return rows
def main():
    parser = FolderParser()
    parser.feed(fetch('https://drive.google.com/drive/folders/'+FOLDER).decode('utf-8'))
    if len(parser.files) < 4: raise ValueError('Drive listing incomplete or inaccessible; existing dashboard preserved')
    with tempfile.TemporaryDirectory(prefix='cpi-refresh-') as temp:
        stage = pathlib.Path(temp); (stage/'dist').mkdir(); inputs = stage/'inputs'; inputs.mkdir()
        shutil.copy2(ROOT/'prepare.py',stage/'prepare.py')
        shutil.copy2(ROOT/'price_series.py',stage/'price_series.py')
        source_files=[]
        for entry in sorted(parser.files.values(), key=lambda e:e['name']):
            ident=entry['id']
            url = ('https://docs.google.com/spreadsheets/d/'+ident+'/export?format=xlsx' if entry['kind']=='sheet'
                   else 'https://drive.usercontent.google.com/download?id='+ident+'&export=download')
            raw=fetch(url)
            if not zipfile.is_zipfile(io.BytesIO(raw)): raise ValueError('Not an Excel workbook: '+entry['name'])
            name=pathlib.Path(entry['name']).name
            if not name.lower().endswith('.xlsx'): name+='.xlsx'
            (inputs/name).write_bytes(raw)
            source_files.append(dict(entry,sha256=hashlib.sha256(raw).hexdigest()))
            print('Downloaded:', name)
        for name,url,required in [
            ('cpi.csv','https://storage.dosm.gov.my/cpi/cpi_2d_state.csv',{'state','date','division','index'}),
            ('cpi_national.csv','https://storage.dosm.gov.my/cpi/cpi_2d.csv',{'date','division','index'}),
            ('divisions.csv','https://storage.dosm.gov.my/dictionaries/mcoicop.csv',{'digits','division','desc_en'})]:
            raw=fetch(url);validate_csv(raw,required);(stage/'dist'/name).write_bytes(raw)
        subprocess.run([sys.executable,str(stage/'prepare.py')],env=dict(os.environ,PRICE_INPUT_DIR=str(inputs)),check=True)
        cpi=json.loads((stage/'dist/cpi.json').read_text()); prices=json.loads((stage/'dist/prices.json').read_text())
        if not any(r[0]=='Malaysia' for r in cpi['rows']): raise ValueError('Malaysia CPI missing')
        if not any(r[0]=='Malaysia' for r in prices['rows']): raise ValueError('Malaysia prices missing')
        # Avoid silently dropping history if a source file is removed or its structure changes.
        for name,new in [('cpi.json',cpi),('prices.json',prices)]:
            old_path=ROOT/'dist'/name
            if old_path.exists():
                old=json.loads(old_path.read_text(encoding='utf8'))
                key=lambda r:tuple(r[:3] if name=='cpi.json' else r[:4])
                old_keys={key(r) for r in old['rows']}; new_keys={key(r) for r in new['rows']}
                if not old_keys.issubset(new_keys): raise ValueError(name+': historical observations disappeared; review source before accepting')
            keys=[tuple(r[:3] if name=='cpi.json' else r[:4]) for r in new['rows']]
            if len(keys)!=len(set(keys)): raise ValueError('Duplicate observations: '+name)
        previous_path=ROOT/'dist/update-status.json'
        previous=json.loads(previous_path.read_text()) if previous_path.exists() else {}
        changed=any(not (ROOT/'dist'/n).exists() or (ROOT/'dist'/n).read_bytes()!=(stage/'dist'/n).read_bytes() for n in ['cpi.json','prices.json','divisions.csv'])
        status={'last_successful_refresh':datetime.now(timezone.utc).isoformat() if changed or not previous else previous['last_successful_refresh'],
                'cpi_latest':max(r[1] for r in cpi['rows']), 'prices_latest':max(r[1] for r in prices['rows']),
                'drive_folder':'https://drive.google.com/drive/folders/'+FOLDER,'files':source_files}
        # No live files are changed until every download, parse and check above passes.
        for name in ['cpi.csv','cpi_national.csv','divisions.csv','cpi.json','prices.json']:
            dest=ROOT/'dist'/name; temporary=dest.with_suffix(dest.suffix+'.tmp')
            shutil.copy2(stage/'dist'/name,temporary);os.replace(temporary,dest)
        if changed or not previous:
            previous_path.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('Refresh complete:',status['cpi_latest'],status['prices_latest'])
if __name__=='__main__':main()
