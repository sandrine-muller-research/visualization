*** README ***

To run this app you need to have Python installed on your machine.
If you do not have these packages, please install them before running the code.

** Package installation (in the local OS terminal) **
pip install pandas
pip install numpy
pip install plotly
pip install matplotlib
pip install adjustText
pip install streamlit

** Run app **
At the local OS command prompt, run the following command to launch a local web browser:
streamlit run volcano\plotvolcano.py

** GUI **
1) load your (.csv) file and indicate the name of the columns containing
    (a) the log fold-change,
    (b) the p-values,
    (c) the adjusted p-values for multiple comparisons, and
    (d) the names of the genes or features.
2) Click Go! It will take a few seconds to load your file in the viewer.
3) Change visualization parameters to your preference on the left side.
    The changes will happen only once you validate them (Click Go again!)
4) Download your results using the links on the left side of the volcano plot.
