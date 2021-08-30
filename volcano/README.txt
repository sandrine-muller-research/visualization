*** README ***

To run this app you need to have python installed on your machine. 

** Packages installation **
Packages needed:
pandas
numpy
matplotlib
adjustText
streamlit

If you do not have this packages, please install them before running the code (pip install package in the terminal)


** Run app **
Once the packages are up and running:
1) on the command line go to the code location
2) run the following command to launch a local web browser
streamlit run plotvolcano.py 


** GUI **
1) load your (.csv) file and indicate the name of the columns containing (i)the log fold-change, (ii) the p-values, (iii) the adjusted p-values for multiple comparisons, (iv) the name of the genes. Then click Go! It will take a few second to load your file in the viewer.
2) change visualization parameters to your convenience on the left side. The changes will happen only once you validate them (click on Go!)
3) Download your results using the links on the left side of the Volcano plot. 
