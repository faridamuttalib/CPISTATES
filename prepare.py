import openpyxl, glob, json, csv, pathlib, collections, os
from price_series import annotate
root=pathlib.Path(__file__).parent
months=['januari','februari','mac','april','mei','jun','julai','ogos','september','oktober','november','disember']
records={}; sources=[]
for f in sorted(pathlib.Path(os.environ.get('PRICE_INPUT_DIR', str(root.parent))).glob('*.xlsx')):
 w=openpyxl.load_workbook(f,read_only=True,data_only=True); count=0
 for s in w:
  rows=list(s.values)
  header=next((i for i,r in enumerate(rows[:12]) if any(str(v).strip()=='NO.' for v in r)),None)
  if header is None: continue
  years=rows[header]; ms=rows[header+1]; dates={}; year=None
  for c in range(4,len(ms)):
   if c<len(years) and isinstance(years[c],(int,float)) and 2000<years[c]<2100: year=int(years[c])
   m=str(ms[c]).strip().lower()
   if year and m in months: dates[c]=f'{year}-{months.index(m)+1:02d}-01'
  state=s.title.strip().title().replace('Wp ','W.P. ')
  category=''; previous_item=None
  for r in rows[header+2:]:
   if len(r)<4: continue
   continuation=r[1] is None and r[2] and r[3] and str(r[2]).strip()==previous_item
   if not isinstance(r[1],(int,float)) and not continuation:
    if r[2] and not r[3]: category=str(r[2]).strip()
    elif isinstance(r[1],str) and not r[2]: category=r[1].strip()
    continue
   if not r[2] or not r[3]: continue
   item=str(r[2]).strip(); unit=str(r[3]).strip()
   previous_item=item
   for c,d in dates.items():
    if c<len(r) and isinstance(r[c],(int,float)) and r[c]>0:
     records[(state,d,item,unit)]=[state,d,item,unit,float(r[c]),category]; count+=1
 sources.append({'file':f.name,'observations':count})
price_rows=list(records.values())
families=annotate(price_rows)
with open(root/'dist/prices.json','w',encoding='utf8') as f: json.dump({'rows':price_rows,'sources':sources,'families':families},f,ensure_ascii=False,separators=(',',':'))
with open(root/'dist/cpi.csv',encoding='utf-8-sig') as f: cpi=list(csv.DictReader(f))
with open(root/'dist/cpi_national.csv',encoding='utf-8-sig') as f:
 cpi.extend(dict(r,state='Malaysia') for r in csv.DictReader(f))
with open(root/'dist/divisions.csv',encoding='utf-8-sig') as f: labels={r['division']:r['desc_en'] for r in csv.DictReader(f) if r['digits'] in ['1','2']}
with open(root/'dist/cpi.json','w') as f: json.dump({'rows':[[r['state'],r['date'],r['division'],float(r['index'])] for r in cpi if r['index']], 'labels':labels},f,separators=(',',':'))
print(json.dumps({'cpi_rows':len(cpi),'cpi_latest':max(r['date'] for r in cpi),'price_rows':len(records),'price_latest':max(k[1] for k in records),'sources':sources}))
