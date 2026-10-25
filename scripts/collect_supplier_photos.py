from pathlib import Path
from urllib.parse import urljoin, urlparse
from io import BytesIO
import csv, json, re, zipfile, time
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

SITES={
 'Gamma':'https://deckart.su/katalog/',
 'Alpha-Beta':'https://euro-deck.ru/shop/catalog/terrasnaya-doska/',
 'Mars':'https://mastodeck.ru/',
 'SM':'https://cottage-mode.ru/'
}
session=requests.Session()
session.headers.update({'User-Agent':'Mozilla/5.0 (compatible; NimTechProductPhotoReview/1.0)'})
root=Path('supplier-photo-review');root.mkdir(exist_ok=True)
catalog=json.loads(Path('src/data/catalog.json').read_text(encoding='utf-8'))
rows=[]; visited=set()
def get(url):
 try:
  r=session.get(url,timeout=18);r.raise_for_status()
  if 'text/html' not in r.headers.get('Content-Type',''):return None
  return BeautifulSoup(r.text,'html.parser')
 except Exception:return None
def category(name):
 return next((k for k,v in SITES.items() if k in name),None)
for source,start in SITES.items():
 queue=[start]; count=0; image_count=0
 while queue and count<45 and image_count<130:
  url=queue.pop(0)
  if url in visited:continue
  visited.add(url); count+=1
  soup=get(url)
  if soup is None:continue
  title=(soup.title.get_text(' ',strip=True) if soup.title else '')[:180]
  for a in soup.select('a[href]'):
   link=urljoin(url,a.get('href','')).split('#')[0]
   if urlparse(link).netloc==urlparse(start).netloc and link not in visited and link not in queue and len(queue)<200:
    if re.search(r'catalog|katalog|prod|product|terras|dosk|stupen|fasad|zabor|deck|shop',link,re.I):queue.append(link)
  candidates=[]
  for tag in soup.select('img'):
   src=tag.get('data-src') or tag.get('data-lazy-src') or tag.get('src')
   srcset=tag.get('data-srcset') or tag.get('srcset')
   if srcset:
    entries=[x.strip().split(' ') for x in srcset.split(',')]
    entries=[x for x in entries if x]
    if entries:src=entries[-1][0]
   if src:candidates.append((urljoin(url,src),tag.get('alt','')))
  for link in soup.select('a[href]'):
   href=urljoin(url,link.get('href',''))
   if re.search(r'\.(jpg|jpeg|png|webp)(\?|$)',href,re.I):candidates.append((href,''))
  for imgurl,alt in dict.fromkeys(candidates):
   if image_count>=130:break
   try:
    r=session.get(imgurl,timeout=18);r.raise_for_status()
    if len(r.content)>14000000:continue
    im=Image.open(BytesIO(r.content))
    if im.width<650 or im.height<350:continue
    if im.width/im.height>4 or im.height/im.width>4:continue
    im=ImageOps.exif_transpose(im).convert('RGB')
    im.thumbnail((1800,1800),Image.Resampling.LANCZOS)
    folder=root/source;folder.mkdir(exist_ok=True)
    name=f'{source.lower().replace("-","_")}-{image_count+1:03d}.webp'
    im.save(folder/name,'WEBP',quality=90,method=6)
    rows.append([source,title,url,imgurl,alt,im.width,im.height,f'{source}/{name}','REVIEW_REQUIRED'])
    image_count+=1
   except Exception:pass
  time.sleep(.12)
 print(source,'pages',count,'candidate_images',image_count)
with (root/'manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['supplier','page_title','product_page','original_image_url','alt','width','height','archive_path','status']);w.writerows(rows)
(root/'README.txt').write_text('Candidate supplier images only. Review exact product, profile and color against NimTech/MoySklad before publishing. No images automatically assigned to products. Original resolution is never artificially upscaled. GR uses NimTech office photography. Confirm image reuse rights with suppliers.\n',encoding='utf-8')
with zipfile.ZipFile('nimtech-supplier-photo-review.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in root.rglob('*'):
  if p.is_file():z.write(p,arcname=str(p.relative_to(root)))
print('Total',len(rows))
