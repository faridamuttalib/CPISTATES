"""Curated item families; original workbook labels and prices remain in columns 0–5."""
import collections,re
ALIASES={
 'Ikan Kembong':'Ikan Kembung','Kobis Bulat':'Kubis Bulat','Kobis Bunga':'Kubis Bunga',
 'Kalian':'Kailan','Nenas':'Nanas','Mee Kering':'Mi Kering',
 'Potong Rambut (Lelaki)':'Mengunting Rambut (Lelaki)', 'Menggunting Rambut (Lelaki)':'Mengunting Rambut (Lelaki)',
 'Keju (12) PK':'Keju (12) Pek','Bayam':'Bayam Hijau','Air Minuman':'Air Mineral',
 'Cili (Burung/padi) Import':'Cili Padi Burung (Import)', 'Daging Lembu':'Daging Lembu Tempatan',
 'Epal (Green Skin)':'Epal Hijau','Epal (Red Skin, Gala)':'Epal Merah','Ketam':'Ketam Bunga',
 'Cecair pembasmi kuman':'Pensanitasi Tangan','Shampoo, 320 ML':'Syampu',
 'Sawi, Bunga (Choy Sum)':'Sawi Jepun', 'Telur Gred A':'Telur Ayam Gred A',
 'Telur Gred B':'Telur Ayam Gred B','Telur Gred C':'Telur Ayam Gred C',
 'Televisyen Warna, LED 40"':'Televisyen Warna, Full HD 40"-43"'
}
# Only clear spelling/wording changes with unchanged units share a comparison segment.
SAFE={'Ikan Kembong','Kobis Bulat','Kobis Bunga','Kalian','Nenas','Mee Kering',
      'Potong Rambut (Lelaki)','Menggunting Rambut (Lelaki)','Keju (12) PK',
      'Telur Gred A','Telur Gred B','Telur Gred C'}
UNIT_FAMILIES={'Kopi-O','Milo','Teh Tarik','Teh-O','Mayonis','Pelembut Fabrik','Makanan Haiwan','Syampu','Periuk Nasi Elektrik, 1.8LT','Tisu Tandas'}
def clean(s):return re.sub(r'\s+',' ',s).strip()
def annotate(rows):
 families={}; preceding_units={}
 for r in rows:
  if r[1]<'2024-01-01':
   n=clean(r[2]).replace(' *','').rstrip('*').strip();k=(r[0],n)
   if k not in preceding_units or r[1]>preceding_units[k][0]:preceding_units[k]=(r[1],clean(r[3]))
 for r in rows:
  raw=clean(r[2]); name=raw.replace(' *','').rstrip('*').strip(); unit=clean(r[3]); canonical=ALIASES.get(name,name)
  if name=='Sabun Mandi': family='Sabun Mandi · '+('bar' if 'Pek 3' in unit else 'cecair')
  elif name=='Tuala Wanita':family='Tuala Wanita · '+('pek kecil' if unit in ['Pek 10','Pek 16'] else 'pek besar')
  elif canonical in UNIT_FAMILIES:family=canonical
  else:family=canonical+' | '+unit
  # Workbook explicitly dates these unit changes to August 2024; the row label
  # contains the later unit across all columns. Use the preceding unit before then.
  if r[1]<'2024-08-01' and r[1]>='2024-01-01':
   if name=='Pelembut Fabrik':unit='2 L Bot'
   elif name=='Makanan Haiwan':unit='450 gm'
   elif name=='Tisu Tandas':unit=preceding_units.get((r[0],name),('', '8 Gulung'))[1]
   elif name=='Sabun Mandi' and 'Pek 3' in unit:unit='1 Pek 3, 85 gm'
  # A changed label/specification starts a new comparison segment unless it is
  # a reviewed spelling-only alias. Never convert or backcast observed prices.
  definition=(canonical if name in SAFE or name in SAFE_TARGETS else name)+' | '+unit
  if name in ['Beras SST 5%','Periuk Nasi Elektrik, 1.8LT','Ubat Nyamuk','Tuala Wanita'] and r[1]>='2025-03-01' and ('*' in raw):
   definition+=' | specification from Mar 2025'
  r.extend([family,definition,unit])
  info=families.setdefault(family,{'label':family,'first':r[1],'last':r[1],'definitions':{}})
  info['first']=min(info['first'],r[1]);info['last']=max(info['last'],r[1])
  v=info['definitions'].setdefault(definition,{'name':name,'unit':unit,'first':r[1],'last':r[1],'source_labels':[]})
  v['first']=min(v['first'],r[1]);v['last']=max(v['last'],r[1])
  if raw not in v['source_labels']:v['source_labels'].append(raw)
 seen=set()
 for r in rows:
  key=(r[0],r[1],r[6])
  if key in seen:raise ValueError('Ambiguous family mapping: '+str(key))
  seen.add(key)
 for info in families.values():info['definitions']=sorted(info['definitions'].values(),key=lambda x:(x['first'],x['name']))
 return families
SAFE_TARGETS={ALIASES[n] for n in SAFE}
