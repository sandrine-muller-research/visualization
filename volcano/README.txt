*** README ***

To run this app you need to have Python installed on your machine.
If you do not have these packages, please install them before running the code.

** Package installation (in the local OS terminal) **
pip install pandas
pip install numpy
pip install matplotlib
pip install adjustText
pip install streamlit

** Run app **
At the local OS command prompt, run the following command to launch a local web browser:
streamlit run plotvolcano.py
(you need to be in the 'volcano' folder)

** GUI **
1) load your (.csv) file and indicate the name of the columns containing (i)the log fold-change, (ii) the p-values, (iii) the adjusted p-values for multiple comparisons, (iv) the name of the genes. Then click Go! It will take a few second to load your file in the viewer.
2) change visualization parameters to your convenience on the left side. The changes will happen only once you validate them (click on Go!)
3) Download your results using the links on the left side of the Volcano plot.
