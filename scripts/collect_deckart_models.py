#!/usr/bin/env python3
"""Download original images from exact Deckart model pages for manual review."""
import csv, io, re, time, zipfile
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT="https://deckart.su/"
MODELS={
 "Gamma_DOUBLE_139x27":["практикум оптимум","praktikum optimum","optimum","139х27","139x27"],
 "Gamma_PC_150x24":["практик new","practik new","praktik new","150х24","150x24"],
 "Gamma_MG_165x32":["магнум new","magnum new","mangum new","165х32","165x32"],
 "Gamma_LIGHT_140x20":["практик лайт","practik light","praktik light","140х20","140x20"],
}
S=requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (compatible; NimTechCatalogReview/1.0)"})
def get(url):
 try:
  r=S.get(url,timeout=25);r.raise_for_status();return r
 except Exception as e:
  print("SKIP",url,str(e));return None
def norm(s):return re.sub(r"\\s+"," ",s.lower().replace("×","x").replace("х","x"))
def discover():
 queue=[ROOT];seen=set();found={}
 while queue and len(seen)<250:
  url=queue.pop(0)
  if url in seen:continue
  seen.add(url)
  r=get(url)
  if not r:continue
  soup=BeautifulSoup(r.text,"html.parser")
  title=norm(" ".join([soup.title.get_text(" ",strip=True) if soup.title else "",soup.find("h1").get_text(" ",strip=True) if soup.find("h1") else ""]))
  body=norm(soup.get_text(" ",strip=True)[:2500])
  for model,terms in MODELS.items():
   if any(norm(t) in title for t in terms):found.setdefault(model,[]).append((url,soup))
  for a in soup.select("a[href]"):
   href=urljoin(url,a["href"]).split("#")[0]
   p=urlparse(href)
   if p.netloc not in ("deckart.su","www.deckart.su") or not p.path.startswith("/"):continue
   if re.search(r"\\.(?:jpg|jpeg|png|webp|pdf|zip|svg|gif)$",p.path,re.I):continue
   if href not in seen and href not in queue and len(queue)<1500:queue.append(href)
  time.sleep(.1)
 return found
def main():
 found=discover();out=Path("deckart-model-photos.zip");rows=[]
 with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for model,pages in found.items():
   unique=set();n=0
   for page,soup in pages[:12]:
    candidates=[]
    for tag in soup.select("img,source"):
     for key in ("data-src","data-original","data-large_image","src","srcset","data-srcset"):
      val=tag.get(key)
      if not val:continue
      for item in val.split(","):
       src=item.strip().split(" ")[0]
       if src and not src.startswith("data:"):candidates.append(urljoin(page,src))
    for tag in soup.select("a[href]"):
     href=urljoin(page,tag["href"])
     if re.search(r"\\.(jpg|jpeg|png|webp)(?:\\?|$)",href,re.I):candidates.append(href)
    for src in candidates:
     if src in unique:continue
     unique.add(src)
     r=get(src)
     if not r or len(r.content)>12000000:continue
     try:
      im=Image.open(io.BytesIO(r.content))
      if im.width<650 or im.height<350:continue
      im.load();im=im.convert("RGB")
      n+=1;name=f"{model}/{n:03d}.jpg"
      buf=io.BytesIO();im.save(buf,"JPEG",quality=93,optimize=True)
      z.writestr(name,buf.getvalue())
      rows.append([model,name,page,src,im.width,im.height,"REVIEW_REQUIRED"])
     except Exception:continue
   print(model,len(pages),"pages",n,"photos")
  csvbuf=io.StringIO();w=csv.writer(csvbuf);w.writerow(["model","file","product_page","image_url","width","height","status"]);w.writerows(rows)
  z.writestr("manifest.csv",csvbuf.getvalue().encode("utf-8-sig"))
  z.writestr("README.txt","Candidates from matching Deckart model pages. Verify profile and color before publication. No catalog changes.\n")
 print("Saved",out,len(rows),"photos")
if __name__=="__main__":main()
