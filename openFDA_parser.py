def parser_event(data):

    df = {
        'report_number' :[], 
        'date_received' :[],
        'manufacturer_g1_name' :[],
        'brand_name' :[],
        'device_name' :[],
        'product_code' :[],
        'product_problems' :[],
        'patient_problems' :[],
        'text' :[]
    }

    for record in data:

        df['report_number'].append(record.get('report_number'))
        df['manufacturer_g1_name'].append(record.get('manufacturer_g1_name'))
        df['date_received'].append(record.get('date_received'))
        
        try:
            device_field = record.get('device', [{}])[0]
            df['brand_name'].append(device_field.get('brand_name', ''))
            df['device_name'].append(device_field.get('openfda', {}).get('device_name', ''))
            df['product_code'].append(device_field.get('device_report_product_code', ''))
        except:
            df['brand_name'].append('')
            df['device_name'].append('')
            df['product_code'].append('')

        df['product_problems'].append(record.get('product_problems'))
        try:
            df['patient_problems'].append(record.get('patient')[0].get('patient_problems'))
        except:
            df['patient_problems'].append('')

        try: 
            mdr_text_0 = record['mdr_text'][0]['text']
        except:
            mdr_text_0 = ''
        
        try:
            mdr_text_1 = record['mdr_text'][1]['text']
        except:
            mdr_text_1 = ''

        mdr_text =  f'{mdr_text_1} {mdr_text_0}'
        df['text'].append(mdr_text)


    return df


def parser_510k(data):
    df = {
        'device_name' : [],
        'product_code' : [],
        'applicant' : [],
        'openfda_device' : [],
        'k_number' : [],
        'date_received' : [],
        'clearance_type' : [],
        'decision_description' : []
    }


    for report in data:

            df['device_name'].append(report.get('device_name'))
            df['product_code'].append(report.get('product_code'))
            df['applicant'].append(report.get('applicant'))
            df['openfda_device'].append(report.get('openfda').get('device_name'))
            df['k_number'].append(report.get('k_number'))
            df['date_received'].append(report.get('date_received'))
            df['clearance_type'].append(report.get('clearance_type'))
            df['decision_description'].append(report.get('decision_description'))

    return df


def parser_udi(data):
    df = {
    'public_device_record_key' : [],
    'commercial_distribution_status' : [],
    'k_number' : [],
    'device_description' : [],
    'company_name' : [],
    'brand_name' : [],
    'public_version_date' : []
    }

    for record in data:

        df['public_device_record_key'].append(record.get('public_device_record_key'))
        df['commercial_distribution_status'].append(record.get('commercial_distribution_status'))
        try:
            df['k_number'].append(record.get('premarket_submissions')[0].get('submission_number'))
        except:
            df['k_number'].append('')

        df['device_description'].append(record.get('device_description'))
        df['company_name'].append(record.get('company_name'))
        df['brand_name'].append(record.get('brand_name'))

        df['public_version_date'].append(record.get('public_version_date'))

    return df

def parser_recalls(data):
    df = {
        'event_date_created' :[],
        'recall_status' :[],
        'recalling_firm' :[],
        'product_code' :[],
        'root_cause_description' : [],
        'product_description' : [],
        'action' : [],
        # openfda field
        'device_name' : [],
        'medical_specialty_description' : []
    }

    for record in data:
        df['event_date_created'].append(record.get('event_date_created'))
        df['recall_status'].append(record.get('recall_status'))
        df['recalling_firm'].append(record.get('recalling_firm'))
        df['product_code'].append(record.get('product_code'))
        df['root_cause_description'].append(record.get('root_cause_description'))
        df['product_description'].append(record.get('product_description'))
        df['action'].append(record.get('action'))

        openfda_field = record.get('openfda')
        df['device_name'].append(openfda_field.get('device_name'))
        df['medical_specialty_description'].append(openfda_field.get('medical_specialty_description'))
    return df