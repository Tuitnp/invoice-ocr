"""Conservative bilingual invoice field extraction. Missing fields remain null."""
import re
from decimal import Decimal, InvalidOperation

DIGITS = str.maketrans('๐๑๒๓๔๕๖๗๘๙', '0123456789')
LABELS = {
 'company_name': r'(?:ชื่อบริษัท|ผู้ขาย|ผู้ออกใบแจ้งหนี้|company\s*name|seller|supplier|vendor)',
 'customer_name': r'(?:ชื่อลูกค้า|ลูกค้า|ผู้ซื้อ|เรียกเก็บเงิน(?:ไปยัง)?|customer(?:\s*name)?|guest\s+name\b|bill\s*to|buyer|sold\s*to)',
 'invoice_number': r'(?:เลขที่(?:ใบแจ้งหนี้|เอกสาร|ใบกำกับภาษี)?|ใบแจ้งหนี้เลขที่|invoice\s*(?:number|no\.?|#)|document\s*(?:no\.?|number)|^no\.?\s*[:：])',
 'invoice_date': r'(?:วันที่(?:ออก(?:เอกสาร|ใบแจ้งหนี้))?|invoice\s*date|date)',
}
ALL_LABEL = re.compile('|'.join(LABELS.values()) + r'|ยอดรวม|total|ที่อยู่|address|tax\s*id|เลขประจำตัว', re.I)

def extract_fields(text):
 lines = [re.sub(r'[ \t]+', ' ', s).strip() for s in text.translate(DIGITS).splitlines() if s.strip()]
 out = {k: None for k in (*LABELS, 'total_amount')}
 for key, pattern in LABELS.items():
  regex = re.compile((r'^' if key in ('company_name','customer_name') else r'(?<![A-Za-z])') + pattern + r'\s*[:：#]?\s*(.*)', re.I)
  for i, line in enumerate(lines):
   if key == 'invoice_date' and re.search(r'due\s*date|วันที่ครบกำหนด|วันครบกำหนด',line,re.I): continue
   m = regex.search(line)
   if not m: continue
   value = m.group(1).strip(' :：|-')
   if not value and i+1 < len(lines) and not ALL_LABEL.match(lines[i+1]): value = lines[i+1]
   # Avoid consuming the adjacent label in OCR rows.
   value = re.split(r'\s+(?:วันที่|invoice date|date|tax id|เลขประจำตัว)\s*[:：]?', value, flags=re.I)[0].strip()
   if key == 'invoice_number':
    n = re.match(r'[A-Za-z0-9][A-Za-z0-9/_.-]*', value)
    value = n.group() if n else ''
   if value:
    out[key] = value
    break
 if not out['company_name']:
  for line in lines[:10]:
   if re.search(r'บริษัท|ห้างหุ้นส่วน|\b(?:co\.?[,]?\s*ltd\.?|limited|ltd\.?|inc\.?|corporation)\b', line, re.I) and not re.search(LABELS['customer_name'], line, re.I):
    out['company_name'] = line
    break
 candidates=[]
 for i,line in enumerate(lines):
  if re.search(r'ยอดรวมสุทธิ|จำนวนเงิน(?:รวม)?ทั้งสิ้น|ยอดสุทธิ|รวม(?:เงิน)?ทั้งสิ้น|grand\s*total|amount\s*due|total\s*(?:amount|due)|net\s*total',line,re.I): priority=3
  elif re.search(r'ยอดรวม|รวมเงิน|(?<![a-z])total(?![a-z])',line,re.I) and not re.search(r'sub\s*total|ก่อนภาษี|ส่วนลด|discount',line,re.I): priority=1
  else: continue
  portion=line
  if not re.search(r'\d',portion) and i+1<len(lines): portion=lines[i+1]
  nums=re.findall(r'(?<![\w.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?(?![\w.])',portion)
  if nums:
   try: candidates.append((priority,i,format(Decimal(nums[-1].replace(',','')),'.2f')))
   except InvalidOperation: pass
 if candidates: out['total_amount']=max(candidates)[2]
 return out
