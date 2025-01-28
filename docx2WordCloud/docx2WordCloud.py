import sys, os
from datetime import datetime

import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

from docx import Document
import spacy
import tkinter as tk
from tkinter import filedialog, messagebox

def select_file(title):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title=title, filetypes=[("All files", "*.*")])
    return file_path

def read_docx_omitting_titles(file_path_str):
    doc = Document(file_path_str)
    text_content = []

    for i, paragraph in enumerate(doc.paragraphs):
        if 'Heading' not in paragraph.style.name:  
            text_content.append(paragraph.text)

    full_text = "\n".join(text_content)
    
    return full_text


def create_and_save_plot(wordcloud_obj,save_path):
    
    plt.figure(figsize=(12, 6))
    plt.imshow(wordcloud_obj, interpolation='bilinear')
    plt.axis('off')

    plt.savefig(save_path)
    return print(f"Plot saved to {save_path}")

def contains_number(string):
    return any(char.isdigit() for char in string)
    
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python docx2WordCloud.py <docx_input_path_string> <save_path_string>")
        # get arguments if not given:
        input_path = select_file("Select input file")
        base_path = os.path.dirname(os.path.abspath(input_path))

        # dialog box to select if the user wants to save the figure
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno("Title", "Do you want to output wordcloud .jpg image?")
        
        if result:
            filename_no_ext = os.path.splitext(os.path.basename(input_path))[0]
            save_path = os.path.join(base_path,filename_no_ext + '_wordcloud_image.jpg')
            save_path_keywords = os.path.join(base_path,filename_no_ext + "_keywords.txt")
            save_path_keywords_parameters = os.path.join(base_path,filename_no_ext + "_keywords_parameters.txt")
        else:
            save_path = " "

    elif len(sys.argv) == 3:
        input_path = r"{}".format(sys.argv[1])
        save_path = r"{}".format(sys.argv[2])
        save_path_keywords = os.path.normpath(save_path.replace('jpg', 'txt'))
        save_path_keywords_parameters = os.path.normpath(save_path.replace('.jpg', '_parameters.txt'))
        
    if save_path == " ":
        base_path = os.path.dirname(input_path)
        save_path_keywords = os.path.join(base_path,os.sep,"keywords.txt")
        save_path_keywords_parameters = os.path.join(base_path,os.sep,"keywords_parameters.txt")
    
    input_path = os.path.normpath(r"{}".format(input_path))
    save_path = os.path.normpath(r"{}".format(save_path))

    text = read_docx_omitting_titles(input_path)
    if isinstance(text,str):
        all_words = text.split()
        all_words_no_numbers = [word for word in all_words if not contains_number(word)]

        nlp = spacy.load("en_core_web_sm")
        doc = nlp(' '.join(all_words_no_numbers))
        doc_no_stop_words = [token for token in doc if not token.is_stop]
        compound_words = [chunk.text for chunk in doc.noun_chunks]
        
        total_number_words = len(compound_words)
        max_words = round(0.02 * total_number_words)
        
        wordcloud = WordCloud(
        background_color='white',
        width=800,
        height=400,
        max_words=50,
        contour_color='steelblue',  
        contour_width=1
        ).generate(' '.join(compound_words))
        
        keywords_list = list(wordcloud.words_.keys())
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # save outputs:        
        with open(save_path_keywords, "w") as file:
            file.write("\n".join(keywords_list) + "\n")
                
        with open(save_path_keywords_parameters, "w") as file:
            file.write(f"file generated on {current_timestamp}\n")
            file.write(f"List of generated files with parameters: \n{save_path}\n{save_path_keywords}\n")
            file.write("interpolation : bilinear\n")
            file.write(f"total compound words found : {total_number_words}\n")
            file.write(f"calculated cutoff keywords: {max_words}\n")

        if save_path != " ":
            create_and_save_plot(wordcloud,save_path)





