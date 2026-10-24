from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import csv, zipfile
src=Path('public/images/catalog')
out=Path('nimtech-catalog-enhanced')
out.mkdir(exist_ok=True)
rows=[]
for p in sorted(src.iterdir()):
 if p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):continue
 try:
  im=Image.open(p).convert('RGBA')
  bg=Image.new('RGBA',im.size,'white')
  bg.alpha_composite(im)
  im=bg.convert('RGB')
  # Preserve product proportions and avoid cropping product geometry.
  im=ImageOps.contain(im,(1500,1100),Image.Resampling.LANCZOS)
  if im.width<1100:
   scale=min(2.4,1100/im.width)
   im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
  im=ImageEnhance.Contrast(im).enhance(1.045)
  im=ImageEnhance.Sharpness(im).enhance(1.18)
  im=im.filter(ImageFilter.UnsharpMask(radius=1.4,percent=90,threshold=3))
  canvas=Image.new('RGB',(1500,1100),'white')
  canvas.paste(im,((1500-im.width)//2,(1100-im.height)//2))
  dest=p.stem+'.webp'
  canvas.save(out/dest,'WEBP',quality=93,method=6)
  rows.append([p.name,dest,'ok'])
 except Exception as e:rows.append([p.name,'','ERROR: '+str(e)])
with (out/'mapping.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['original_filename','enhanced_filename','status']);w.writerows(rows)
(out/'README.txt').write_text('NimTech product images: normalized white background, 1500x1100, WebP.\\nUpload only *.webp to public/images/catalog/.\\nIMPORTANT: processing improves presentation and edge sharpness but cannot restore missing detail in tiny originals.\\nOriginal files are retained on GitHub; site must be switched to .webp filenames after upload.\\n',encoding='utf-8')
with zipfile.ZipFile('nimtech-catalog-enhanced.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in out.iterdir():z.write(p,arcname=p.name)
print('Processed',sum(r[2]=='ok' for r in rows),'of',len(rows))
