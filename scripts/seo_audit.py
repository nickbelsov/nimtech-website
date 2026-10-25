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
 route='/' if rel=='index.astro' else '/'+re.sub(r'(?:/index)?\\.astro$','',rel).strip('/')+'/'
 routes[route]=p
redirects={r for r,p in routes.items() if 'http-equiv="refresh"' in p.read_text()}
issues=[]
titles=defaultdict(list);descriptions=defaultdict(list)
def flag(level,route,msg):issues.append((level,route,msg))
for route,p in routes.items():
 s=p.read_text()
 if route in redirects:continue
 h1=len(re.findall(r'<h1(?:\\s|>)',s,re.I))
 if h1!=1:flag('HIGH',route,f'H1: {h1}')
 for key,bucket in [('title',titles),('description',descriptions)]:
  match=re.search(r'const '+key+r'\\s*=\\s*([\'\"])(.*?)\\1',s,re.S)
  if match:bucket[match.group(2)].append(route)
 for m in re.finditer(r'<a\\b[^>]*href=[\'\"]([^\'\"]+)[\'\"][^>]*>(.*?)</a>',s,re.S|re.I):
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
 for m in re.finditer(r'<img\\b[^>]*src=[\'\"](/[^\'\"]+)[\'\"]',s,re.I):
  path=m.group(1)
  if not (ROOT/'public'/path.lstrip('/')).exists():flag('HIGH',route,'Missing image: '+path)
for key,values in [('title',titles),('description',descriptions)]:
 for value,rs in values.items():
  if len(rs)>1:flag('HIGH',', '.join(rs),'Duplicate '+key+': '+value[:100])
blog=[r for r in routes if r.startswith('/blog/') and r!='/blog/' and r not in redirects]
lines=['# NimTech static SEO audit','','Pages: '+str(len(routes)),'Blog articles: '+str(len(blog)),'HTML redirect pages: '+str(len(redirects)),'Findings: '+str(len(issues)),'','Note: source-level checks only; not live HTTP, CWV, JS execution or full semantic SEO.','','| Priority | Route | Finding |','|---|---|---|']
lines += ['| '+level+' | '+route.replace('|','/')+' | '+msg.replace('|','/')+' |' for level,route,msg in sorted(issues)]
Path('seo-audit-report.md').write_text('\\n'.join(lines)+'\\n')
print('\\n'.join(lines[:10]))
