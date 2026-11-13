import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1400,'height':1000},accept_downloads=True)
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8092/')
 page.screenshot(path=str(ROOT/'artifacts/desktop-empty.png'),full_page=True)
 page.locator('#file').set_input_files(str(ROOT/'tests/fixtures/invoice-th.png'))
 page.locator('#read').click()
 page.locator('#result-state.done').wait_for(timeout=30000)
 assert page.locator('[name=total_amount]').input_value()=='10700.00'
 assert page.locator('[name=customer_name]').input_value()=='บริษัท กรีนการ์เด้น จำกัด'
 page.locator('[name=company_name]').fill('ชื่อที่แก้ไขเพื่อทดสอบ')
 with page.expect_download() as pending: page.locator('#json').click()
 target=ROOT/'artifacts/test-export.json';pending.value.save_as(str(target))
 assert json.loads(target.read_text())['fields']['company_name']=='ชื่อที่แก้ไขเพื่อทดสอบ'
 with page.expect_download() as pending: page.locator('#csv').click()
 target=ROOT/'artifacts/test-export.csv';pending.value.save_as(str(target))
 assert target.read_text(encoding='utf-8-sig').startswith('"company_name"')
 page.screenshot(path=str(ROOT/'artifacts/desktop-result.png'),full_page=True)
 page.locator('#reset').click()
 assert page.locator('#read').is_disabled()
 page.locator('#file').set_input_files(str(ROOT/'tests/fixtures/invoice-en.pdf'))
 page.locator('#read').click()
 page.locator('#result-state.done').wait_for(timeout=30000)
 assert page.locator('[name=total_amount]').input_value()=='10700.00'
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 page.screenshot(path=str(ROOT/'artifacts/mobile-result.png'),full_page=True)
 assert not errors,errors
 browser.close()
 print('Browser checks passed: upload, OCR, edit, JSON/CSV export, reset, PDF, mobile layout; no JavaScript errors.')
