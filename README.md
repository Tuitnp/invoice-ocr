# Invoice desk

เว็บอ่านใบแจ้งหนี้ไทยและอังกฤษแบบเรียบง่าย: JPG, PNG, WEBP, PDF →
ชื่อบริษัท, ชื่อลูกค้า, ยอดรวม, เลขที่ใบแจ้งหนี้, วันที่
แก้ไขผลลัพธ์และส่งออก JSON/CSV (UTF-8 BOM สำหรับ Excel) ได้

## ที่ติดตั้ง

- Source: `/root/invoice-ocr`
- Runtime: `/opt/invoice-ocr` (service user `invoice-ocr`, read-only filesystem)
- App: `127.0.0.1:8092` ผ่าน systemd `invoice-ocr.service`, เริ่มเองหลัง reboot
- Nginx: `/etc/nginx/sites-available/invoice.tanapat.dev`
- Domain: `invoice.tanapat.dev`

เพิ่ม DNS zone record (ไม่ได้แก้ zone ให้):

```dns
invoice 300 IN A 213.35.98.114
```

DNS ปัจจุบันเปิด Cloudflare proxy อยู่ ติดตั้ง certificate ของ
`invoice.tanapat.dev` และ HTTPS reverse proxy เรียบร้อยแล้ว ทดสอบผ่าน Cloudflare
ได้ทั้งหน้าเว็บและ API; certbot timer เดิมของเครื่องจะต่ออายุ certificate ให้
ตัว bootstrap `invoice-ocr-https.timer` ปิดแล้วหลังตั้งค่า HTTPS สำเร็จ
ไม่ได้เพิ่ม login; ผู้ที่เข้าถึง URL สามารถอัปโหลดเอกสารได้

```bash
systemctl status invoice-ocr
nginx -t
certbot certificates
curl -fsS https://invoice.tanapat.dev/api/health
```

## OCR

ใช้ [iapp/OpenThai2.0-OCR-Text](https://huggingface.co/iapp/OpenThai2.0-OCR-Text)
Apache-2.0, ONNX Runtime บน CPU ไม่ต้องใช้ API key และไม่ส่งเอกสารไป OCR API
ยึด model/runtime commit `39fa41bdd49f067ba41b1d9de79c06ab506d67d4`
พร้อม SHA-256 checksums ใน `model-checksums.json`; notices อยู่ใน `models/NOTICE`

ขั้นแรกอ่านภาพเป็นข้อความ ขั้นที่สองดึง 5 ช่องด้วยกฎคำกำกับไทย/อังกฤษ
ช่องที่ไม่พบจะเป็น null; ไม่มีการแปลชื่อบริษัท/ลูกค้า หรือเปลี่ยนปี พ.ศ./ค.ศ.
ยอดรวมเก็บเป็น string ทศนิยม 2 หลักเพื่อคงความแม่นยำ วันที่เก็บตามต้นฉบับ
รองรับข้อความพิมพ์เป็นหลัก ต้องตรวจข้อมูลก่อนใช้งาน โดยเฉพาะ 0/O และลายมือ
เอกสารหลายหน้าถือเป็นใบแจ้งหนี้เดียว ใช้แยกอ่านทีละใบ
PDF ถูกแปลงเป็นภาพเพื่อเข้า OCR รวมถึง PDF ที่มี text layer

ไฟล์อัปโหลดอาจใช้ temporary storage ระหว่างรับ request และถูกปิด/ลบหลังประมวลผล
ไม่เก็บประวัติหรือเอกสารถาวร ไม่เขียนข้อความ OCR ลง access log
จำกัด 15 MB, PDF 10 หน้า, ภาพ 24 ล้านพิกเซล, งาน OCR พร้อมกัน 1 งาน
Nginx จำกัดการอ่าน 6 ครั้ง/นาที/IP (burst 3), ปิด request buffering

## Local development

```bash
cd /root/invoice-ocr
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python scripts/download_models.py
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8092
```

พอร์ตนี้ถูกใช้โดย service ที่ติดตั้งอยู่แล้ว หากต้องการ dev พร้อมกันให้ใช้พอร์ตอื่น

## Update deployed code

```bash
cd /root/invoice-ocr
cp app.py extract.py /opt/invoice-ocr/
cp -a static/. /opt/invoice-ocr/static/
systemctl restart invoice-ocr
curl -fsS http://127.0.0.1:8092/api/health
```

ไฟล์ตั้งต้น systemd/Nginx และตัวเปิด HTTPS อยู่ใน `deploy/`.
หลัง Certbot ทำงาน Nginx config จริงจะมี HTTPS เพิ่มเติม อย่าทับด้วยไฟล์ตั้งต้น

## Validation

```bash
.venv/bin/python -m pytest -q
# optional UI checks
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python scripts/browser_check.py
```

ทดสอบ OCR จริงจากภาพและ PDF จำลองทั้งไทย/อังกฤษ รวมกรณี subtotal, Thai digits,
ช่องที่หาย, ไฟล์เสีย และขนาดไฟล์เกินกำหนด ยังไม่ได้ทดสอบใบแจ้งหนี้จริงของผู้ใช้
ภาพหน้าจอ UI และตัวอย่าง export จาก browser checks อยู่ใน `artifacts/`.

API: `POST /api/extract` multipart field `file`; `GET /api/health`.
ผลลัพธ์ประกอบด้วย `fields`, `text`, `pages` (confidence ต่อบรรทัด), `engine`, `warnings`.
