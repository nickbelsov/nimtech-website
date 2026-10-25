#!/usr/bin/env python3
"""Static SEO checks for NimTech Astro pages. Writes an actionable Markdown report."""
from pathlib import Path
from collections import defaultdict
import re
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parents[1]
PAGES=ROOT/'src/pages'
files=sorted(PAGES.rglob('index.astro'))+[PAGES/'index.astro',PAGES/'privacy.astro',PAGES/'personal-data.astro']
files=[p for p in files if p.exists()]
routes={}
for p in files:
 rel=p.relative_to(PAGES).as_posix()
 if rel.startswith('['):continue
 route='/' if rel=='index.astro' else '/'+re.sub(r'(?:/index)?\.astro$','',rel).strip('/')+'/'
 routes[route]=p
redirects={r for r,p in routes.items() if 'http-equiv="refresh"' in p.read_text()}
issues=[]
titles=defaultdict(list);descriptions=defaultdict(list)
def flag(level,route,msg):issues.append((level,route,msg))
for route,p in routes.items():
 s=p.read_text()
 if route in redirects:continue
 h1=len(re.findall(r'<h1(?:\s|>)',s,re.I))
 if h1!=1:flag('HIGH',route,f'H1: {h1}')
 for key,bucket in [('title',titles),('description',descriptions)]:
  match=re.search(r'const '+key+r'\s*=\s*([\'\"])(.*?)\1',s,re.S)
  if match:bucket[match.group(2)].append(route)
 for m in re.finditer(r'<a\b[^>]*href=[\'\"]([^\'\"]+)[\'\"][^>]*>(.*?)</a>',s,re.S|re.I):
  href,anchor=m.groups()
  if href.startswith(('#','mailto:','tel:','https:','http:','javascript:')):continue
  path=unquote(urlsplit(href).path)
  if not path.startswith('/'):continue
  if not path.endswith('/') and '.' not in path.split('/')[-1]:path+='/'
  if path not in routes and not (ROOT/'public'/path.lstrip('/')).exists():
   flag('HIGH',route,'Possibly broken internal link: '+href)
  text=re.sub(r'<[^>]+>','',anchor).strip()
  if re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+){2,}',text):
   flag('MEDIUM',route,'Slug-like anchor: '+text)
 for m in re.finditer(r'<img\b[^>]*src=[\'\"](/[^\'\"]+)[\'\"]',s,re.I):
  path=m.group(1)
  if not (ROOT/'public'/path.lstrip('/')).exists():flag('HIGH',route,'Missing image: '+path)
for key,values in [('title',titles),('description',descriptions)]:
 for value,rs in values.items():
  if len(rs)>1:flag('HIGH',', '.join(rs),'Duplicate '+key+': '+value[:100])
blog=[r for r in routes if r.startswith('/blog/') and r!='/blog/' and r not in redirects]

# Verify the complete blog cover inventory and sitemap consistency.
blog_slugs={r.split('/')[2] for r in blog}
cover_dir=ROOT/'public/images/blog/covers'
cover_slugs={p.stem for p in cover_dir.glob('*.webp')} if cover_dir.exists() else set()
for slug in sorted(blog_slugs-cover_slugs):
 flag('HIGH','/blog/'+slug+'/','Missing article cover: '+slug+'.webp')
for slug in sorted(cover_slugs-blog_slugs):
 flag('MEDIUM','/images/blog/covers/','Orphan cover: '+slug+'.webp')
sitemap=(PAGES/'sitemap.xml.ts').read_text()
sitemap_urls=set(re.findall(r"'/blog/([^/]+)/'",sitemap))
for slug in sorted(blog_slugs-sitemap_urls):
 flag('HIGH','/sitemap.xml','Article missing from sitemap: '+slug)
for slug in sorted(sitemap_urls-blog_slugs):
 flag('MEDIUM','/sitemap.xml','Sitemap references non-article or redirect: '+slug)
blog_index=(PAGES/'blog/index.astro').read_text()
index_slugs=set(re.findall(r'slug:["\\\']([^"\\\']+)["\\\']',blog_index))
for slug in sorted(blog_slugs-index_slugs):
 flag('HIGH','/blog/','Article missing from blog index: '+slug)
for slug in sorted(index_slugs-blog_slugs):
 flag('HIGH','/blog/','Blog index references missing article: '+slug)
for slug in sorted(blog_slugs):
 article=(PAGES/'blog'/slug/'index.astro').read_text()
 if 'BlogPosting' not in article:flag('MEDIUM','/blog/'+slug+'/','Missing BlogPosting structured data')
 if 'BreadcrumbList' not in article:flag('MEDIUM','/blog/'+slug+'/','Missing BreadcrumbList structured data')
 if 'type="article"' not in article:flag('MEDIUM','/blog/'+slug+'/','Missing article Open Graph type')

lines=['# NimTech static SEO audit','','Pages: '+str(len(routes)),'Blog articles: '+str(len(blog)),'HTML redirect pages: '+str(len(redirects)),'Findings: '+str(len(issues)),'','Note: source-level checks only; not live HTTP, CWV, JS execution or full semantic SEO.','','| Priority | Route | Finding |','|---|---|---|']
lines += ['| '+level+' | '+route.replace('|','/')+' | '+msg.replace('|','/')+' |' for level,route,msg in sorted(issues)]
Path('seo-audit-report.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[:10]))
