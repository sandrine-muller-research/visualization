import sys
# from inspect import getsourcefile
# from os.path import abspath
import os
from pathlib import Path

import streamlit as st

import pandas as pd
# import numpy as np
import matplotlib.pyplot as plt
from rdkit import Chem
from rdkit.Chem import Draw


import requests

import yaml
import base64
from io import BytesIO
import uuid
import re

# from pysmiles import read_smiles
# import networkx as nx

# required installations
# rdkit,streamlit
# pip install torch==1.11.0+cu113 torchvision==0.11.1+cu113 torchaudio==0.10.0+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html

# Variables
BASE_URL = 'https://molepro.broadinstitute.org/molecular_data_provider'
cpd_config_file = 'biochem_compound_card.json'
# fileP = abspath(getsourcefile(lambda:0))

########################## CLASSES:
######################################## TRANSLATOR:
class Compound:

    def __init__(self,data):
        self.name = self.get_compound_name(data)
        self.description = self.get_compound_desc(data)
        self.smiles = self.get_smiles(data)
        # self.fill_compound_structure('/util/entities/compound_MolePro_attribute_type_mapping.yml')
    
    def fill_compound_structure(self):
        with open(os.getcwd()+cpd_config_file) as f:
            compound_config = yaml.load(f, Loader=yaml.FullLoader)
            print(compound_config)
        
    
    def get_compound_name(self,data):
        ''' merge all compound name descriptions with sources'''
        cpd = get_compound(data)
        if cpd != None:
            if 'attributes' in cpd:
                if len(cpd['names_synonyms']) !=0:
                    cpd_names = [c['name'] for c in cpd['names_synonyms'] if c['name'] != None]
                    cpd_synonyms = []
                    cpd_synonyms = [cpd_synonyms + c['synonyms'] for c in cpd['names_synonyms'] if c['synonyms'] != None]
                cpd_name = max(set(cpd_names+cpd_synonyms[0]), key = cpd_names.count)
            else:
                cpd_name = cpd['id']
        else:
            cpd_name = None
        
        return cpd_name
    
    def get_smiles(self,in_json):

        cpd = get_compound(in_json)
        if 'identifiers' in cpd:
            if 'smiles' in in_json['elements'][0]['identifiers']:
                compound_smiles = in_json['elements'][0]['identifiers']['smiles']
        else:
            compound_smiles = None

        return compound_smiles
    
    def get_compound_desc(self,data):
        ''' get most prevalent compound name'''
        cpd_att = get_cpd_att(data)
        cpd_desc = list()
        if cpd_att != None:
            for idx,t in enumerate(cpd_att):
                if (t['attribute_type_id'] == "description")&(t['value'] != None):
                    src_link = get_source_link(t['provided_by'])
                    source = t['attribute_source']
                    if len(source)==0:
                        source = ''
                    else:
                        source = source.replace('infores','source')
                    text = t['value']
                    if len(text)==0:
                        text = ''
                    cpd_desc.append({'source':source,'link':src_link,'text':text})
        else:
            cpd_desc = '' 
        
        return cpd_desc     

######################################## GUI:
class CompoundCard:

    def __init__(self):
        st.set_page_config(layout="wide")

    def construct_app(self,cpd):
        # compound identity
        st.markdown('#' + cpd.name)
        col1, col2 = st.columns(2)
        smile_fig = plot_mol(cpd.smiles)
        col1.pyplot(smile_fig)
        
        show_text(cpd.description,col2,'Summary')
            
            
########################## FUNCTIONS:
######################################## TRANSLATOR:
def get_example_url():
    query = ['Metformin']
    results = requests.post(BASE_URL + '/compound/by_name', json=query).json()
    return [results['url']]

def get_source_link(transformer_name):
    transformers_info = requests.get('https://translator.broadinstitute.org/molecular_data_provider/transformers').json()
    transformer_url = [t['properties']['source_url'] for t in transformers_info if t['name']== transformer_name]
    if len(transformer_url)== 0:
        transformer_url = ''
    else:
        transformer_url = transformer_url[0]
    return transformer_url

def get_identifiers(in_json):
    cpd = get_compound(in_json)
    if cpd != None:
        if 'identifiers' in cpd:
            h_df = cpd['identifiers']
        else:
            h_df = None
    else:
        h_df = None
    
    return h_df

def get_compound(in_json): # only for the first element
    if 'elements' in in_json:
        if len(in_json['elements'])>0:
            cpd = in_json['elements'][0]
        else:
            cpd = None
    else:
        cpd = None
    return cpd

def get_cpd_att(in_json):
    cpd = get_compound(in_json)
    if 'attributes' in cpd:
            cpd_att = cpd['attributes']
    else:
        cpd_att = None
    return cpd_att

######################################## OPERATIONS:
def save_df_xlsx(df,sheet_name):
    output = BytesIO()
    writer = pd.ExcelWriter(output)
    df.to_excel(writer,sheet_name)
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def plot_mol(smiles):
    
    fig, ax = plt.subplots()
    fig.set_size_inches(1, 1)
    
    mol = Chem.MolFromSmiles(smiles)
    fig = Draw.MolToMPL(mol)
    plt.axis('off')
    
    ax.set_box_aspect(1)
    
    return fig

def module_path():
    encoding = sys.getfilesystemencoding()
    return os.path.dirname(unicode(__file__, encoding))

######################################## GUI:
def create_st_button(link_text, link_url, hover_color="#c8bfe7", st_col=None):

    button_uuid = str(uuid.uuid4()).replace("-", "")
    button_id = re.sub("\d+", "", button_uuid)

    button_css = f"""
        <style>
            #{button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 0px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }}
            #{button_id}:hover {{
                border-color: {hover_color};
                color: {hover_color};
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: {hover_color};
                color: white;
                }}
        </style> """

    html_str = f'<a href="{link_url}" target="_blank" id="{button_id}";>{link_text}</a><br></br>'

    if st_col is None:
        st.markdown(button_css + html_str, unsafe_allow_html=True)
    else:
        st_col.markdown(button_css + html_str, unsafe_allow_html=True)

def show_text(my_text_list_dict,loc,title):
    for d in my_text_list_dict:
        loc.markdown("---")
        loc.markdown(""" ### """ + title)
        create_st_button(d['source'], d['link'], st_col=loc)
        loc.markdown(d['text'])

def get_table_download_link(df,sheet_name):
    # adapted from: https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806/17
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = save_df_xlsx(df,sheet_name)
    b64 = base64.b64encode(val)
    return f'<a style="font-family:Arial; color:Black; font-size: 12px;" href="data:application/octet-stream;base64,{b64.decode()}" download="downloadable-table-file.xlsx">{sheet_name}</a>'


########################## FUNCTIONS END
def vect_2_str_in_dict(my_dict,sep):
    for i in my_dict.keys():
        if isinstance(my_dict[i], list):
            my_dict[i] = sep.join(my_dict[i])
    return my_dict

     

def main(compound_collection_url):
    
    
    data = requests.get(compound_collection_url[0]).json()
  
    # compound attributes:
    cpd = Compound(data)
    
    sa = CompoundCard()
    sa.construct_app(cpd)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args)>0:
        main(args)
    else:
        ex_url = get_example_url()
        print(ex_url)
        main(ex_url)