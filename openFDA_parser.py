def parser_event(data):
    report_number, date_received, manufacturer_d_name, brand_name, device_name, product_problems, patient_problems, text = [], [], [], [], [], [], [], []

    for record in data:

        report_number.append(record['report_number'])
        try:
            manufacturer_d_name.append(
                record['device'][0]['manufacturer_d_name'])
        except:
            manufacturer_d_name.append('')

        try:
            date_received.append(record['date_received'])
        except:
            date_received.append('')

        try:
            brand_name.append(record['device'][0]['brand_name'])
        except:
            brand_name.append('')

        try:
            device_name.append(record['device'][0]['openfda']['device_name'])
        except:
            device_name.append('')

        try:
            product_problems.append(record['product_problems'])
        except:
            product_problems.append('')

        try:
            patient_problems.append(record['patient'][0]['patient_problems'])
        except:
            patient_problems.append('')
        
        try: 
            mdr_text_0 = record['mdr_text'][0]['text']
        except:
            mdr_text_0 = ''
        
        try:
            mdr_text_1 = record['mdr_text'][1]['text']
        except:
            mdr_text_1 = ''

        mdr_text =  f'{mdr_text_1} {mdr_text_0}'
        text.append(mdr_text)

    df = {
        'report_number': report_number,
        'date_received': date_received,
        'manufacturer_d_name': manufacturer_d_name,
        'brand_name': brand_name,
        'device_name': device_name,
        'product_problems': product_problems,
        'patient_problems': patient_problems,
        'text': text
    }

    return df


def parser_510k(data):
    device_name = []
    product_code = []
    applicant = []
    openfda_device = []
    k_number = []
    date_received = []
    clearance_type = []
    decision_description = []

    for report in data:
        try:
            device_name.append(report['device_name'])
            product_code.append(report['product_code'])
            applicant.append(report['applicant'])
            openfda_device.append(report['openfda']['device_name'])
            k_number.append(report['k_number'])
            date_received.append(report['date_received'])
            clearance_type.append(report['clearance_type'])
            decision_description.append(report['decision_description'])
        except:
            device_name.append('')
            product_code.append('')
            applicant.append('')
            openfda_device.append('')
            k_number.append('')
            date_received.append('')
            clearance_type.append('')
            decision_description.append('')

    df = {'device_name': device_name, 'product_code': product_code,
          'applicant': applicant, 'openfda_device': openfda_device,
          'k_number': k_number, 'date_received': date_received,
          'clearance_type': clearance_type, 'decision_description': decision_description}
    return df


def parser_udi(data):
    public_device_record_key = []
    commercial_distribution_status = []
    k_number = []
    device_description = []
    company_name = []
    brand_name = []
    public_version_date = []

    for record in data:
        try:
            public_device_record_key.append(record['public_device_record_key'])
        except:
            public_device_record_key.append('')
        try:
            commercial_distribution_status.append(
                record['commercial_distribution_status'])
        except:
            commercial_distribution_status.append('')
        try:
            k_number.append(record['premarket_submissions']
                            [0]['submission_number'])
        except:
            k_number.append('')
        try:
            device_description.append(record['device_description'])
        except:
            device_description.append('')
        try:
            company_name.append(record['company_name'])
        except:
            company_name.append('')
        try:
            brand_name.append(record['brand_name'])
        except:
            brand_name.append('')
        try:
            public_version_date.append(record['public_version_date'])
        except:
            public_version_date.append('')

    df = {'public_device_record_key': public_device_record_key,
          'commercial_distribution_status': commercial_distribution_status,
          'k_number': k_number,
          'device_description': device_description,
          'company_name': company_name,
          'brand_name': brand_name,
          'public_version_date': public_version_date
          }
    return df
