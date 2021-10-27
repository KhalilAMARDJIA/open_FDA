import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

data = pd.read_csv("event_data.csv", sep=";")
data = data.dropna()

def series_freq_plot (pd_series, n = 20):
    df = data['manufacturer_d_name'].value_counts()
    df = pd.DataFrame({'name': df.index, 'n': df.values}).sort_values(by= 'n', ascending= False)
    plot = df.nlargest(n, columns='n').plot.barh(x = 'name', y = 'n').invert_yaxis()
    plt.tight_layout()
    return plot

series_freq_plot(data['manufacturer_d_name'], n = 20)
plt.savefig('manufacturers.pdf')

series_freq_plot(data['brand_name'], n = 20)
plt.savefig('brand.pdf')



def str_pd_series_tolist(pd_series):
    main_list = []
    for item in pd_series:
        lst = item.strip('][').replace("'", "").split(', ')
        main_list += lst
    return main_list


def bar_plot(df, n=20):
    df.nlargest(n, columns='n').plot.barh().invert_yaxis()
    plt.tight_layout()

# Patient problems analysis

patient_problems = str_pd_series_tolist(data['patient_problems'])
patient_problems_df = pd.DataFrame(
    dict(Counter(patient_problems)), index=['n'])
patient_problems_df = patient_problems_df.transpose().sort_values(by='n')

ftr_patient = ['No Code Available', 'No Known Impact Or Consequence To Patient', 'Symptoms or Conditions', 'No Information', 'No Consequences Or Impact To Patient',
               'Appropriate Clinical Signs', 'No Clinical Signs', 'Conditions Term / Code Not Available', 'Insufficient Information', 'No Patient Involvement', 'Reaction', 'Patient Problem/Medical Problem']

patient_problems_df = patient_problems_df.loc[~patient_problems_df.index.isin(
    ftr_patient)]

bar_plot(df=patient_problems_df)
plt.savefig('patient_problems.pdf')


# product problems analysis

product_problems = str_pd_series_tolist(data['product_problems'])
product_problems_df = pd.DataFrame(
    dict(Counter(product_problems)), index=['n'])
product_problems_df = product_problems_df.transpose().sort_values(by='n')

ftr_product = ['Adverse Event Without Identified Device or Use Problem',
               'Appropriate Term/Code Not Available', 'Unknown (for use when the device problem is not known)', 'Insufficient Information', 'No Apparent Adverse Event']

product_problems_df = product_problems_df.loc[~product_problems_df.index.isin(
    ftr_product)]

bar_plot(df=product_problems_df)
plt.savefig('product_problems.pdf')
