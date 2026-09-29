# Dependencies: requests beautifulsoup4 pymupdf
# Existing PDF and extracted text skip download; manifest pins reviewed versions.
from pathlib import Path
import requests,json,hashlib,concurrent.futures,datetime
from bs4 import BeautifulSoup
import pymupdf
root=Path(__file__).resolve().parent
for folder in ['metadata','papers','text']:(root/folder).mkdir(exist_ok=True)
locked={x['name']:x for x in json.loads((root/'manifest.json').read_text())} if (root/'manifest.json').exists() else {}
def run(item):
 name,aid=item
 p=root/'papers'/f'{name}_{aid}.pdf'
 if p.exists() and (root/'text'/f'{name}.txt').exists(): return name,'cached'
 try:
  if name in locked:
   record=locked[name]
   if not p.exists():
    r=requests.get('https://arxiv.org/pdf/'+aid+'v'+str(record['version']),timeout=120);r.raise_for_status()
    if not r.content.startswith(b'%PDF'): raise ValueError('not PDF')
    if hashlib.sha256(r.content).hexdigest()!=record['sha256']: raise ValueError('Downloaded PDF differs from reviewed SHA-256; original manifest preserved')
    p.write_bytes(r.content)
   with pymupdf.open(p) as doc:
    (root/'text'/f'{name}.txt').write_text('\n'.join(f'\n=== PDF PAGE {i+1} ===\n'+page.get_text() for i,page in enumerate(doc)))
   return name,'restored pinned PDF and text'
  html=requests.get('https://arxiv.org/abs/'+aid,timeout=60);html.raise_for_status()
  (root/'metadata'/f'{name}.html').write_text(html.text)
  soup=BeautifulSoup(html.text,'html.parser')
  meta={}
  for m in soup.select('meta[name^="citation_"]'):
   meta.setdefault(m.get('name'),[]).append(m.get('content'))
  pdfurl=(meta.get('citation_pdf_url') or ['https://arxiv.org/pdf/'+aid])[0]
  p=root/'papers'/f'{name}_{aid}.pdf'
  if not p.exists():
   r=requests.get(pdfurl,timeout=120);r.raise_for_status()
   if not r.content.startswith(b'%PDF'): raise ValueError('not PDF')
   p.write_bytes(r.content)
  doc=pymupdf.open(p)
  (root/'text'/f'{name}.txt').write_text('\n'.join(f'\n=== PDF PAGE {i+1} ===\n'+page.get_text(sort=False) for i,page in enumerate(doc)))
  meta.update(arxiv_id=aid,name=name,pdf_url=pdfurl,pages=len(doc),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),history=soup.select_one('.submission-history').get_text(' ',strip=True) if soup.select_one('.submission-history') else '')
  (root/'metadata'/f'{name}.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
  return name,len(doc),meta.get('citation_title'),meta['history']
 except Exception as e: return name,type(e).__name__,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(run,json.loads((root/'paper_list.json').read_text()).items()):print(r,flush=True)
