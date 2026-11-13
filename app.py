import asyncio
import io
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
import pypdfium2 as pdfium
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from extract import extract_fields

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'models'))
MAX_BYTES=15*1024*1024
MAX_PAGES=10
Image.MAX_IMAGE_PIXELS=24_000_000
log=logging.getLogger('invoice')

@asynccontextmanager
async def lifespan(app):
 from runtime.line_engine import LineOCR
 app.state.engine=await run_in_threadpool(lambda: LineOCR(str(ROOT/'models'),threads=2))
 app.state.lock=asyncio.Lock()
 yield

app=FastAPI(title='Invoice OCR',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')

@app.api_route('/',methods=['GET','HEAD'])
def index(): return FileResponse(ROOT/'static/index.html')

@app.get('/api/health')
def health(): return {'status':'ok','engine':'OpenThai2.0-OCR-Text','languages':['th','en']}

def process(data):
 pages=[]
 def read(image):
  image=ImageOps.exif_transpose(image).convert('RGB')
  image.thumbnail((2600,3600))
  result=app.state.engine.read(image)
  return {'text':result['text'],'lines':[{'text':l['text'],'confidence':float(l['confidence'])} for l in result['lines']]}
 if data.startswith(b'%PDF-'):
  try: doc=pdfium.PdfDocument(data)
  except Exception as e: raise ValueError('เปิด PDF ไม่ได้ หรือไฟล์มีรหัสผ่าน / Invalid or encrypted PDF') from e
  try:
   if len(doc)>MAX_PAGES: raise ValueError('รองรับ PDF ไม่เกิน 10 หน้า / Maximum 10 pages')
   for i in range(len(doc)):
    page=doc[i]
    bitmap=None
    try:
     w,h=page.get_size()
     if w<=0 or h<=0: raise ValueError('ขนาดหน้าเอกสารไม่ถูกต้อง / Invalid page size')
     bitmap=page.render(scale=min(2.5,2600/w,3600/h))
     pages.append(read(bitmap.to_pil()))
    finally:
     if bitmap is not None: bitmap.close()
     page.close()
  finally: doc.close()
 else:
  try:
   with Image.open(io.BytesIO(data)) as image:
    if image.format not in ('PNG','JPEG','WEBP'): raise ValueError('รองรับ JPG, PNG, WEBP และ PDF')
    if image.width*image.height>24_000_000: raise ValueError('รูปใหญ่เกิน 24 ล้านพิกเซล / Maximum 24 megapixels')
    pages.append(read(image))
  except (UnidentifiedImageError,Image.DecompressionBombError,Image.DecompressionBombWarning) as e: raise ValueError('ไฟล์ภาพไม่ถูกต้องหรือมีขนาดใหญ่เกินไป / Invalid or oversized image') from e
 text='\n\n'.join(p['text'] for p in pages)
 fields=extract_fields(text)
 return {'fields':fields,'text':text,'pages':pages,'engine':'OpenThai2.0-OCR-Text','warnings':['กรุณาตรวจสอบข้อมูลกับต้นฉบับก่อนใช้งาน / Please verify against the original.'] + (['ไม่พบข้อความที่อ่านได้ / No readable text found.'] if not text.strip() else [])}

@app.post('/api/extract')
async def extract(file:UploadFile=File(...)):
 try:
  data=await file.read(MAX_BYTES+1)
 finally: await file.close()
 if not data: raise HTTPException(400,'ไฟล์ว่าง / Empty file')
 if len(data)>MAX_BYTES: raise HTTPException(413,'ไฟล์ใหญ่เกิน 15 MB / Maximum 15 MB')
 if app.state.lock.locked(): raise HTTPException(429,'กำลังอ่านเอกสารอื่น กรุณาลองอีกครั้ง / Busy, please retry shortly')
 async with app.state.lock:
  try: return await run_in_threadpool(process,data)
  except ValueError as e: raise HTTPException(422,str(e))
  except Exception:
   log.exception('OCR processing failed')
   raise HTTPException(500,'อ่านเอกสารไม่สำเร็จ กรุณาลองไฟล์ที่ชัดขึ้น / Could not read document')
