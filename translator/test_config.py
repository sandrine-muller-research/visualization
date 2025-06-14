import json
import os
import requests
# import transformers as tr
from transformers import pipeline

BASE_URL = 'https://molepro.broadinstitute.org/molecular_data_provider'

# test config_files
def get_example_url():
    query = ['Metformin']
    results = requests.post(BASE_URL + '/compound/by_name', json=query).json()
    return [results['url']]

def fill_with_data(data,config_dict):
    for e in data['elements']:
        for att in e["attributes"]:
            if (att['original_attribute_name'] in config_dict['values'])&(att['value']!=None):
                config_dict['data'] = config_dict['data']+att['original_attribute_name']+'='+att['value']+'(source='+ att['attribute_source'] + ')||'
    return config_dict
    
cpd_url = get_example_url() 
data = requests.get(cpd_url[0]).json()

########## Compound:
cpd_config_file = open(os.getcwd()+'/util/entities/biochem_compound_card.json')
compound_config = json.load(cpd_config_file)
for k,v in compound_config.items():
    if isinstance(v,list):
        for i,conf_dict in enumerate(v):
            if 'data' not in conf_dict:
                conf_dict['data'] = ''
            compound_config[k][i] = fill_with_data(data,conf_dict)
            
    else:
        conf_dict = v
        if 'data' not in conf_dict:
            conf_dict['data'] = ''
        compound_config[k] = fill_with_data(data,conf_dict)
            
        
## creating content:
# gen = pipeline('text-generation', model ='EleutherAI/gpt-neo-2.7B')
gen = pipeline('text-generation', model ='EleutherAI/gpt-neo-125M')
context = "Deep Learning is a sub-field of Artificial Intelligence."
output = gen(context, max_length=50, do_sample=True, temperature=0.9)
print(output)

