from extract import extract_fields

def test_english_total_and_adjacent_date():
 result=extract_fields('Blue River Co., Ltd.\nBill to: Green Garden Ltd.\nInvoice No: INV-001 Date: 13/11/2026\nSubtotal 9,999.00\nGrand Total 10,698.93\nTotal discount 20.00')
 assert result=={'company_name':'Blue River Co., Ltd.','customer_name':'Green Garden Ltd.','invoice_number':'INV-001','invoice_date':'13/11/2026','total_amount':'10698.93'}

def test_thai_multiline_labels_and_digits():
 result=extract_fields('บริษัท ทดสอบ จำกัด\nชื่อลูกค้า:\nบริษัท ลูกค้า จำกัด\nเลขที่ใบแจ้งหนี้: INV-๐๐๑\nวันที่: ๑๓/๑๑/๒๕๖๙\nรวมเงิน ๑,๐๐๐.๐๐\nยอดรวมสุทธิ ๑,๐๗๐.๐๐')
 assert result['company_name']=='บริษัท ทดสอบ จำกัด'
 assert result['customer_name']=='บริษัท ลูกค้า จำกัด'
 assert result['invoice_number']=='INV-001'
 assert result['invoice_date']=='13/11/2569'
 assert result['total_amount']=='1070.00'

def test_missing_fields_do_not_invent_values():
 assert all(v is None for v in extract_fields('สินค้า\nVAT 7%\n10,000.00').values())

def test_missing_customer_does_not_consume_next_label():
 result=extract_fields('ชื่อลูกค้า:\nวันที่: 13/11/2569\nยอดรวมสุทธิ: 0.00')
 assert result['customer_name'] is None
 assert result['total_amount']=='0.00'
