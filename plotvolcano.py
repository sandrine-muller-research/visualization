#/usr/bin/python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict
from matplotlib.colors import ListedColormap
from adjustText import adjust_text
import streamlit as st
import base64
from io import BytesIO
import os
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

# pip install streamlit

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
    # adapted from here: https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806/17
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    val = save_df_xlsx(df,sheet_name)
    b64 = base64.b64encode(val)  
    return f'<a style="font-family:Arial; color:Black; font-size: 12px;" href="data:application/octet-stream;base64,{b64.decode()}" download="Your_File.xlsx">{sheet_name}</a>' 

def get_image_download_link(img):
    # https://www.codegrepper.com/code-examples/python/streamlit+download+image
    """Generates a link allowing the PIL image to be downloaded
    in:  PIL image
    out: href string
    """
    buffered = BytesIO()
    img.savefig (buffered, dpi=600)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a style="font-family:Arial; color:Black; font-size: 12px;" href="data:file/jpg;base64,{img_str}"  download="Your_File.png">volcano plot</a>'
    return href

class VolcanoApp:

    def __init__(self):
        st.set_page_config(layout="wide")

    def get_header_names(self,col1, col2, col3, col4):
        FCvar = col1.text_input("Column name for log fold change", "logFC_norm")
        pvaluevar = col2.text_input("Column name for the p-values", "pvalue")
        FWERvar = col3.text_input("Column name for the p-values adjusted for family-wise error", "padj")
        genenamesvar = col4.text_input("Column name for the genes", "gene_approved_symbol")
        return FCvar, pvaluevar, FWERvar, genenamesvar

    def file_selector(self):
        formfile = st.form(key='file_selector_form')
        formfile.markdown('<p class="header-style">Data file</p>',unsafe_allow_html=True)
        path_in = formfile.file_uploader("Upload a file", type=("csv"))

        col1, col2, col3, col4 = formfile.columns(4)
        FCvar, pvaluevar, FWERvar, genenamesvar = self.get_header_names(col1, col2, col3, col4)

        submit_button = formfile.form_submit_button(label='Go!') 
        return path_in, FCvar, pvaluevar, FWERvar, genenamesvar

    def extract_data(self,path_in,FCvar, pvaluevar, FWERvar, genenamesvar):
        if path_in is not None:
            d = pd.read_csv(path_in,index_col=False,na_values=0)
            FC = d[FCvar].values #logFC_norm.values
            pvalue = -np.log10(d[pvaluevar].values) # d.pvalue
            FWER = d[FWERvar] # d.padj
            genes = d[genenamesvar].values.tolist() #.gene_approved_symbol.values.tolist()
        else:
            FC = np.empty((1,2))
            pvalue = np.empty((1,2))
            FWER = np.empty((1,2))
            genes = ["",""]
            d = None
        return d,FC, pvalue,FWER,genes

    def plot_volcano(self,log_fold_change,log_p_value,gene_names,marker_size,col_idx,colormap_choice,transparency,adjust):
        fig, ax = plt.subplots()
        fig.set_size_inches(5.5, 5.5)
        colors = plt.get_cmap(colormap_choice)
        newcmp = ListedColormap([(0.8,0.8,0.8),colors(0)])
        
        mask = [x!=0 for x in col_idx.tolist()]
        texts = [plt.text(log_fold_change[i], log_p_value[i], gene_names[i]) for (i, v) in zip(range(len((gene_names))),mask) if v]
        plt.scatter(log_fold_change, log_p_value, s=marker_size, c = np.abs(col_idx),cmap=newcmp, alpha=transparency)
        plt.xlabel('log2(Fold Change)')
        plt.ylabel('-log10(pvalue)')

        if adjust:
            adjust_text(texts,arrowprops=dict(arrowstyle="-", color=newcmp(0), lw=0.5))

        ax.set_box_aspect(1)
        return fig

    def construct_sidebar(self):

        form = st.sidebar.form(key='my_form')
        form.markdown('<p class="header-style">Parameters</p>',unsafe_allow_html=True)

        cmaps = colormap_dict()
        cmaps_choice = form.selectbox("Select colormap",cmaps['Qualitative'])

        thsigFC = form.number_input('Threshold for log2(fold change)',min_value=0.0,max_value=100.0,value = 1.0)
        thsigpval = form.number_input('Threshold for -log10(p-value)',min_value=0.0,max_value=1.0,value = 0.05)
        alpha = form.number_input('Marker transparency',min_value=0.0,max_value=1.0,value = 0.7)
        marker_size = form.number_input('Marker size',min_value=0.0,max_value=100.0,value = 30.0)
        adj = form.checkbox("Label auto-adjust - takes few minutes")
        submit_button = form.form_submit_button(label='Go!')

        return thsigFC, thsigpval, cmaps_choice,alpha,marker_size,adj
    
    def construct_app(self):
        
        thsigFC, thsigpval, cmaps_choice,transp,mkr_size,adj = self.construct_sidebar()
        path_in, FCvar, pvaluevar, FWERvar, genenamesvar = self.file_selector()
        # path_in = 'C:/Users/sandrine/Documents/proj/diabetes/data/exp01/dtan/14-13_DE.csv'
        d,FC, pvalue,FWER,genes = self.extract_data(path_in,FCvar, pvaluevar, FWERvar, genenamesvar)

        if path_in is not None:
            color_index = ((np.double(FC>thsigFC))+(-np.double(-FC>thsigFC)))*np.double(FWER<thsigpval)
        else:
            color_index = np.array([0.0,0.0])

        fig = self.plot_volcano(FC,pvalue,genes,mkr_size,color_index,cmaps_choice,transp,adj)

        st.markdown(
            '<p class="font-style" >Volcano plot</p>',
            unsafe_allow_html=True
        )

        col1, col2 = st.columns((1,4))
        col2.plotly_chart(fig,use_container_width=True)

        if path_in is not None:
            idx_pos = [x>0 for x in color_index.tolist()]
            genes_pos = d[idx_pos]
            idx_neg = [x<0 for x in color_index.tolist()]
            genes_neg = d[idx_neg]
            col1.markdown(get_table_download_link(genes_pos,"positive significant geneset"), unsafe_allow_html=True)
            col1.markdown(get_table_download_link(genes_neg,"negative significant geneset"), unsafe_allow_html=True)
            col1.markdown(get_image_download_link(fig), unsafe_allow_html=True)

def main():
    sa = VolcanoApp()
    sa.construct_app()


if ( __name__ == "__main__"):
    main()   

