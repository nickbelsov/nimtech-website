import json,urllib.request,zipfile,io,csv,time,os
from pathlib import Path
manifest=json.loads(Path('src/data/catalog-image-source-manifest.json').read_text())
out=Path('catalog-photos');out.mkdir(exist_ok=True)
rows=[]
for item in manifest:
 for im in item['images']:
  dest=f"{item['id']}-{im['index']:02d}.png"
  status='failed'
  for url in [im.get('url'),im.get('original')]:
   if not url:continue
   try:
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=30) as resp: data=resp.read()
    if len(data)<100 or data[:4] not in [b'\\x89PNG',b'\\xff\\xd8\\xff\\xe0',b'RIFF'] and not data.startswith(b'\\xff\\xd8'):raise ValueError('invalid image')
    ext='.png' if data.startswith(b'\\x89PNG') else '.jpg' if data.startswith(b'\\xff\\xd8') else '.webp'
    dest=f"{item['id']}-{im['index']:02d}{ext}"
    (out/dest).write_bytes(data);status='ok';break
   except Exception as e:status=str(e)[:120]
  rows.append({'product_id':item['id'],'product_name':item['name'],'source_filename':im['filename'],'file':dest if status=='ok' else '', 'status':status,'source_url':im.get('url','')})
with (out/'index.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['product_id']);w.writeheader();w.writerows(rows)
with (out/'README.txt').open('w',encoding='utf-8') as f:f.write('NimTech — изображения каталога из МойСклад.\\nФайлы названы по ID товара. index.csv связывает фотографии с товарами.\\nНе все товары имеют фотографии. Проверьте соответствие цвета модификации перед публикацией.\\n')
with zipfile.ZipFile('nimtech-catalog-photos.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in out.iterdir():z.write(p,arcname=p.name)
print('Photos:',sum(x['status']=='ok' for x in rows),'/',len(rows))
