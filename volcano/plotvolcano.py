#/usr/bin/python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
from matplotlib.colors import ListedColormap
from adjustText import adjust_text
from pandas.core.frame import DataFrame
import streamlit as st
import base64
from io import BytesIO
import os
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import requests
import altair as alt
import json

# Variables
BASE_URL = ['https://translator.broadinstitute.org/molecular_data_provider','http://chembio-dev-01:9200/molecular_data_provider']


def colormap_dict():
    cmaps = OrderedDict()
    cmaps['Perceptually Uniform Sequential'] = [
        'viridis', 'plasma', 'inferno', 'magma', 'cividis']

    cmaps['Sequential'] = [
        'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
        'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
        'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']
    cmaps['Sequential (2)'] = [
        'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
        'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
        'hot', 'afmhot', 'gist_heat', 'copper']
    cmaps['Diverging'] = [
        'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
        'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']
    cmaps['Cyclic'] = ['twilight', 'twilight_shifted', 'hsv']
    cmaps['Qualitative'] = ['Pastel1', 'Pastel2', 'Paired', 'Accent',
        'Dark2', 'Set1', 'Set2', 'Set3',
        'tab10', 'tab20', 'tab20b', 'tab20c']
    return cmaps

def save_df_xlsx(df,sheet_name):
    output = BytesIO()
    writer = pd.ExcelWriter(output)
    df.to_excel(writer,sheet_name)
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df,sheet_name):
    # adapted from: https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806/17
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = save_df_xlsx(df,sheet_name)
    b64 = base64.b64encode(val)
    return f'<a style="font-family:Arial; color:Black; font-size: 12px;" href="data:application/octet-stream;base64,{b64.decode()}" download="downloadable-table-file.xlsx">{sheet_name}</a>'

def get_image_download_link(img):
    # https://www.codegrepper.com/code-examples/python/streamlit+download+image
    """Generates a link allowing the PIL image to be downloaded
    in:  PIL image
    out: href string
    """
    buffered = BytesIO()
    img.savefig (buffered, dpi=600)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a style="font-family:Arial; color:Black; font-size: 12px;" href="data:file/jpg;base64,{img_str}"  download="downloadable-image-file.png">volcano plot</a>'
    return href

def pathways_json_to_df(in_json, geneset_size):
    # inspired from GeLiNEA notebook, authors: Ayushi, Vlado
    # function to reformat GeLiNEA results into a data frame
    # Vlado: For p-value correction, you want to multiply by the number of genesets -
    # 4731 for C2, 5917 for C5, and 50 for H.
    h_df = pd.DataFrame(columns = ['id', 'gene_list_overlap', 'gene_list_connections','GeLiNEA_p_value','GeLiNEA_p_adj'])
    df_size = in_json['size']
    for i in range(0,df_size):
        attr = {attr['original_attribute_name']:attr['value'] for attr in in_json['elements'][i]['connections'][0]['attributes']}
        if (float(attr['GeLiNEA p-value']) * geneset_size) < 0.5:
            h_df = h_df.append({'id' : in_json['elements'][i]['id'],
                                'gene_list_overlap' : attr['gene-list overlap'],
                                'gene_list_connections' : attr['gene-list connections'],
                                'GeLiNEA_p_value': float(attr['GeLiNEA p-value']),
                                'GeLiNEA_p_adj': float(attr['GeLiNEA adjusted p-value']) * geneset_size
                            },
                            ignore_index = True)
    return h_df

def MolePro_query_genelist(gene_list):
    print(gene_list)
    genes_str = ';'.join(gene_list)
    base_url = 'https://translator.broadinstitute.org/molecular_data_provider' #'http://chembio-dev-01:9200/molecular_data_provider' #
    controls = [{'name':'genes', 'value':genes_str}]
    query = {'name':'HGNC gene-list producer', 'controls':controls}
    gene_list_json = requests.post(base_url+'/transform', json=query).json()

    return gene_list_json

def MolePro_run_GeLiNEA(gene_list_json,MSigDB_collection,pval_threshold):
    base_url = 'https://translator.broadinstitute.org/molecular_data_provider' #'http://chembio-dev-01:9200/molecular_data_provider' #
    if MSigDB_collection == 'H - hallmark gene sets':
        n_paths = 50
    elif MSigDB_collection == 'C2 - curated gene sets':
        n_paths = 4731
    elif MSigDB_collection == 'C5 - GO gene sets':
        n_paths = 5917
    else:
        n_paths = 0

    controls = [
    {'name':'network', 'value':'STRING-human-700'},
    {'name':'gene-set collection', 'value':MSigDB_collection},
    {'name':'maximum p-value', 'value':pval_threshold}
    ]

    query = {'name':'gene-list network enrichment analysis (GeLiNEA)', 'collection_id':gene_list_json['id'], 'controls':controls}
    pathways = requests.post(base_url+'/transform', json=query).json()
    p = pathways['url']
    p = p.replace('http://localhost:9200/molecular_data_provider',base_url)
    x = requests.get(p).json()
    return x,n_paths

# @st.cache(suppress_st_warning=True)
def dataframe_read_ftype(path_in,ftype, delimiter):

    if ftype == '.csv':
        d = pd.read_csv(path_in) #,index_col=False,na_values=0)
    if ftype == '.tsv':
        d = pd.read_csv(path_in,index_col=False,na_values=0,sep='\t')
    if ftype == '.tab':
        d = pd.read_csv(path_in,index_col=False,na_values=0,sep='\t')
    if ftype == '.txt':
        d = pd.read_csv(path_in,index_col=False,na_values=0,sep=delimiter)
    else:
        d = None

    return d

class VolcanoApp:

    def __init__(self):
        st.set_page_config(layout="wide")

    def get_header_names(self,col1, col2, col3, col4):
        FCvar = col1.text_input("column name: log-fold-change", "logFC_norm")
        pvaluevar = col2.text_input("column name: p-values", "pvalue")
        FWERvar = col3.text_input("column name: adjusted p-values", "padj")
        genenamesvar = col4.text_input("column name: genes", "gene_approved_symbol")
        return FCvar, pvaluevar, FWERvar, genenamesvar

    def get_file_type(self,handle=None):

        if handle == None:
            col1, col2, col3, col4 = st.columns(4)
        else:
            col1,col2,col3,col4 = handle.columns(4)

        # select input type:
        csv_type = col1.checkbox('.csv')
        tsv_type = col2.checkbox('.tsv')
        tab_type = col3.checkbox('.tab')
        txt_type = col4.checkbox('.txt')

        return csv_type,tsv_type,tab_type,txt_type

    def check_file_type(self,path_in,csv_type,tsv_type,tab_type,txt_type):
        filename, file_extension = os.path.splitext(path_in)
        delimiter = None

        if csv_type+tsv_type+tab_type+txt_type > 1:
            st.text("please select only one extension")
        if csv_type:
            if file_extension != ".csv":
                st.text("file extension does not match")
        if txt_type:
            if file_extension == ".txt":
                delimiter = st.text_input("delimiter")
            else:
                st.text("file extension does not match")
        if tsv_type:
            if file_extension != ".tsv":
                st.text("file extension does not match")
        if tab_type:
            if file_extension != ".tab":
                st.text("file extension does not match")

        return file_extension, delimiter

    def headers_selector(self,handle=None):

        # formfile_headers = st.form(key='file_headers_form')
        # formfile_headers.markdown('<p class="header-style">Headers</p>',unsafe_allow_html=True)
        if handle == None:
            st.markdown('<p class="header-style">2. declare input column headers</p>',unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
        else:
            handle.markdown('<p class="header-style">2. declare input column headers</p>',unsafe_allow_html=True)
            col1, col2, col3, col4 = handle.columns(4)


        FCvar, pvaluevar, FWERvar, genenamesvar = self.get_header_names(col1, col2, col3, col4)
        # submit_button2 = formfile_headers.form_submit_button(label='Go!')

        return FCvar, pvaluevar, FWERvar, genenamesvar

    def extract_data(self,d,FCvar, pvaluevar, FWERvar, genenamesvar):
        if d is not None:
            FC = d[FCvar].values #logFC_norm.values
            pvalue = -np.log10(d[pvaluevar].values) # d.pvalue
            FWER = d[FWERvar] # d.padj
            genes = d[genenamesvar].values.tolist() #.gene_approved_symbol.values.tolist()
        else:
            FC = np.empty((1,2))
            pvalue = np.empty((1,2))
            FWER = np.empty((1,2))
            genes = ["",""]

        return FC, pvalue,FWER,genes

    def create_genelists(self,df,status):
        idx_pos = [x>0 for x in status]
        pos_list = df[idx_pos]
        idx_neg = [x<0 for x in status]
        neg_list = df[idx_neg]
        idx_all = [x!=0 for x in status]
        all_list = df[idx_all]
        return pos_list,neg_list,all_list

    def plot_volcano(self,log_fold_change,log_p_value,gene_names,marker_size,col_idx,colormap_choice,transparency,adjust):
        fig, ax = plt.subplots()
        fig.set_size_inches(5.5, 5.5)
        colors = plt.get_cmap(colormap_choice)
        newcmp = ListedColormap([(0.8,0.8,0.8),colors(0)])

        mask = [x!=0 for x in col_idx.tolist()]
        texts = [plt.text(log_fold_change[i], log_p_value[i], gene_names[i]) for (i, v) in zip(range(len((gene_names))),mask) if v]
        plt.scatter(log_fold_change, log_p_value, s=marker_size, c = np.abs(col_idx),cmap=newcmp, alpha=transparency)
        plt.xlabel('log2(fold-change)')
        plt.ylabel('-log10(p-value)')

        if adjust:
            adjust_text(texts,arrowprops=dict(arrowstyle="-", color=newcmp(0), lw=0.5))

        ax.set_box_aspect(1)
        return fig

    def plot_GeLiNEA(self,pathway_df,colormap_choice):

        pathway_name = pathway_df['id'].values
        pvaladj = np.array(pathway_df['GeLiNEA_p_adj'].values.tolist())
        pvaladj[pvaladj>1] = 1
        pvaladj = -np.log10(pvaladj).round(2)

        if pvaladj.size != 0:
            df = DataFrame({'-log10(padj)': pvaladj,'pathways': pathway_name})
            fig = alt.Chart(df).mark_bar().encode(x='-log10(padj):Q',y="pathways:O")
            text = fig.mark_text(align='left',baseline='middle',dx=3).encode(text='-log10(padj):Q') #, format=",.2f"
            fig = fig + text

        else:
            fig = None

        return fig

    def construct_sidebar(self):

        form_volcano = st.sidebar.form(key='form_volcano')
        form_volcano.markdown('<p class="header-style">3. set volcano and gene-list parameters</p>',unsafe_allow_html=True)

        cmaps = colormap_dict()
        cmaps_choice = form_volcano.selectbox("select colormap",cmaps['Qualitative'])

        thsigFC = form_volcano.number_input('threshold for log2(fold change)',min_value=0.0,max_value=100.0,value = 1.0)
        thsigpval = form_volcano.number_input('threshold for -log10(adjusted p-value)',min_value=0.0,max_value=1000.0,value = 1.3)
        alpha = form_volcano.number_input('marker transparency',min_value=0.0,max_value=1.0,value = 0.7)
        marker_size = form_volcano.number_input('marker size',min_value=0.0,max_value=100.0,value = 30.0)
        adj = form_volcano.checkbox("label auto-adjust (takes several minutes)")

        submit_button_volcano = form_volcano.form_submit_button(label='Go!')

        form_gelinea = st.sidebar.form(key='form_gelinea')
        form_gelinea.markdown('<p class="header-style">4. set GeLiNEA enrichment parameters</p>',unsafe_allow_html=True)

        collection = form_gelinea.selectbox('MSigDB collection for enrichment',['H - hallmark gene sets','C2 - curated gene sets','C5 - GO gene sets'])
        maxpval = form_gelinea.number_input('threshold for p-value',min_value=0.0,max_value=1.0,value = 0.05)

        submit_button_GeLiNEA = form_gelinea.form_submit_button(label='Go!')

        return thsigFC, thsigpval, cmaps_choice,alpha,marker_size,adj,collection,maxpval

    def construct_app(self):

        thsigFC, thsigpval, cmaps_choice,transp,mkr_size,adj,MSigDB_collection,pval_threshold = self.construct_sidebar()

        form_file = st.form(key='form_file')
        f = form_file.file_uploader("1. upload a file and declare its type", type=(["tsv","csv","txt","tab","xlsx","xls"]))
        csv_type,tsv_type,tab_type,txt_type = self.get_file_type(form_file)
        FCvar, pvaluevar, FWERvar, genenamesvar = self.headers_selector(form_file)
        submit_button = form_file.form_submit_button(label='Submit')


        if f is not None:
            # d,path_in = self.get_file(f)
            ftype, delimiter = self.check_file_type(f.name,csv_type,tsv_type,tab_type,txt_type)
            d = pd.read_csv(f)
            print(f)
            ftype, delimiter = self.check_file_type(f.name,csv_type,tsv_type,tab_type,txt_type)
            # d = dataframe_read_ftype(f,ftype, delimiter)
            print('////////////////////////////////////////////////////////////')
            print(d)
            print('************************************************************')
            FC, pvalue,FWER,genes = self.extract_data(d,FCvar, pvaluevar, FWERvar, genenamesvar)



            color_index = ((np.double(FC>thsigFC))+(-np.double(-FC>thsigFC)))*np.double(-np.log10(FWER)>thsigpval)
            fig = self.plot_volcano(FC,pvalue,genes,mkr_size,color_index,cmaps_choice,transp,adj)
            st.markdown('<p class="font-style" >volcano plot</p>',unsafe_allow_html=True)
            col1, col2 = st.columns((1,4))
            col2.plotly_chart(fig,use_container_width=True)
        else:
            FCvar = ''
            pvaluevar = ''
            FWERvar = ''
            genenamesvar = ''
            d = None


        if d is not None:
            genes_pos,genes_neg,genes_both = self.create_genelists(d,color_index.tolist()) # get sig. gene lists
            col1.markdown(get_table_download_link(genes_pos,"positive significant gene set"), unsafe_allow_html=True)
            col1.markdown(get_table_download_link(genes_neg,"negative significant gene set"), unsafe_allow_html=True)
            col1.markdown(get_table_download_link(genes_both,"negative and positive significant gene sets"), unsafe_allow_html=True)
            col1.markdown(get_image_download_link(fig), unsafe_allow_html=True)

            col3, col4 = st.columns((1,1))

            ## NEGATIVE SET
            genes_neg_json = MolePro_query_genelist(genes_neg[genenamesvar].values.tolist())
            MSigDB_pathways_neg,MSigDB_n_paths_neg = MolePro_run_GeLiNEA(genes_neg_json,MSigDB_collection,pval_threshold)
            df_pathways_neg = pathways_json_to_df(MSigDB_pathways_neg,MSigDB_n_paths_neg)
            fig_gelinea_neg = self.plot_GeLiNEA(df_pathways_neg,cmaps_choice)
            if fig_gelinea_neg is not None:
                col3.subheader('enrichment (GeLiNEA) negative gene set')
                col3.altair_chart(fig_gelinea_neg,use_container_width=True)
                col3.write(df_pathways_neg)
            else:
                col3.subheader('enrichment (GeLiNEA) negative gene set')
                col3.text('no significant enrichment')

            ## POSITIVE SET
            genes_pos_json = MolePro_query_genelist(genes_pos[genenamesvar].values.tolist())
            MSigDB_pathways_pos,MSigDB_n_paths_pos = MolePro_run_GeLiNEA(genes_pos_json,MSigDB_collection,pval_threshold)
            # with open('data.json', 'w') as outfile:
            #     json.dump(MSigDB_pathways_pos, outfile)
            df_pathways_pos = pathways_json_to_df(MSigDB_pathways_pos,MSigDB_n_paths_pos)
            fig_gelinea_pos = self.plot_GeLiNEA(df_pathways_pos,cmaps_choice)
            if fig_gelinea_pos is not None:
                col4.subheader('enrichment (GeLiNEA) positive gene set')
                col4.altair_chart(fig_gelinea_pos,use_container_width=True)
                col4.write(df_pathways_pos)
            else:
                col4.subheader('enrichment (GeLiNEA) positive gene set')
                col4.text('no significant enrichment')

            ## POSITIVE AND NEGATIVE SETS:
            genes_posneg_json = MolePro_query_genelist(genes_both[genenamesvar].values.tolist())
            MSigDB_pathways_posneg,MSigDB_n_paths_posneg = MolePro_run_GeLiNEA(genes_posneg_json,MSigDB_collection,pval_threshold)
            # with open('data.json', 'w') as outfile:
            #     json.dump(MSigDB_pathways_posneg, outfile)
            df_pathways_posneg = pathways_json_to_df(MSigDB_pathways_posneg,MSigDB_n_paths_posneg)
            fig_gelinea_posneg = self.plot_GeLiNEA(df_pathways_posneg,cmaps_choice)
            if fig_gelinea_posneg is not None:
                st.subheader('enrichment (GeLiNEA) positive and negative gene sets')
                st.altair_chart(fig_gelinea_posneg,use_container_width=True)
                st.write(df_pathways_posneg)
            else:
                st.subheader('enrichment (GeLiNEA) positive and negative gene sets')
                st.text('no significant enrichment')

def main():
    sa = VolcanoApp()
    sa.construct_app()


if ( __name__ == "__main__"):
    main()
