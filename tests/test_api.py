from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import app

@pytest.fixture(scope='module')
def client():
 with TestClient(app) as c: yield c

@pytest.mark.parametrize('lang,ext',[('th','png'),('en','png'),('th','pdf'),('en','pdf')])
def test_real_ocr(client,lang,ext):
 path=Path(__file__).parent/'fixtures'/f'invoice-{lang}.{ext}'
 response=client.post('/api/extract',files={'file':(path.name,path.read_bytes())})
 assert response.status_code==200,response.text
 result=response.json()
 assert result['fields']['total_amount']=='10700.00'
 assert result['fields']['company_name']
 assert result['fields']['customer_name']
 assert result['fields']['invoice_number'].startswith('INV-')
 assert result['fields']['invoice_date']==('13/11/2569' if lang=='th' else '13/11/2026')
 assert len(result['pages'])==1

@pytest.mark.parametrize('data',[b'',b'not an image',b'%PDF-broken'])
def test_invalid_file(client,data):
 assert client.post('/api/extract',files={'file':('bad.png',data)}).status_code in (400,422)

def test_upload_limit(client):
 assert client.post('/api/extract',files={'file':('large.png',b'x'*(15*1024*1024+1))}).status_code==413

def test_health_and_page(client):
 assert client.get('/api/health').json()['engine']=='OpenThai2.0-OCR-Text'
 assert client.get('/').status_code==200
