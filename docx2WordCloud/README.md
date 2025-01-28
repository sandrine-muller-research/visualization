# Docx2WordCloud.py
Sandrine Muller

## WHAT FOR?
Feed a .docx file and get the 2% top keywords contained in the text. 

### Requirements:
Tested with Python 3.9.13
To install required packages run the following command at the command line:
> pip install -r requirements.txt

NB: if the code fails with this error:
OSError: [E050] Can't find model 'en_core_web_sm'. It doesn't seem to be a Python package or a valid path to a data directory.
Make sure you've downloaded the language model:
> python -m spacy download en_core_web_sm

### Assumptions:
- The titles are ignored
- words can be compounded
- stopwords are used to remove common words

### Outputs:
- A list of keywords in a line-separated .txt file
- a text file containing parameters
- (OPT) A .jpg file containing the wordcloud image

## USAGE
### Command line:
#### no arguments:
Navigate to the location of the docxWordCloud.py, then run:
> python docx2WordCloud.py
You will be then prompted to give a .docx that you want to analyze and a dialog box to ask if you want to save the image (.jpg) of the wordcloud.

### with arguments:
#### Output both keywords and wordcloud image:
Navigate to the location of the docxWordCloud.py, then run:
> python docx2WordCloud.py "My/Path/To/The/.docx" "My/Path/For/The/.jpg"

#### Output both keywords only:
Navigate to the location of the docxWordCloud.py, then run:
> python docx2WordCloud.py "My/Path/To/The/.docx" " "
