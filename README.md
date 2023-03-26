Examining Predictors of Educational Outcomes: A Comparison of Traditional and Charter Schools in Arizona
=============
### Author: Calvin Eng
Link to Github Repository-
https://github.com/Econ1680-MLTAEcon-Handlan/project1-Calvineng72

Link to paper-
https://drive.google.com/file/d/1DIbSF5_Z_znnVK-dFhbZKsMROW9JgmLS/view?usp=sharing
## Project Details
The following project seeks to determine the difference in outcomes between traditional and charter schools in arizona. Using datasets containing the percent proficient on state exams and school data for every school in Arizona, the project uses machine learning techniques, such as clustering and lasso, to describe the differences between charter and traditional schools. For the original dataset, please contact me at calvin_eng@brown.edu, as the original datasets are too large to be added to GitHub in their form. 
## Files and Folders
The following is a guide to the various files and folders within the repository

- descriptive_statistics.ipynb contains the methods used to initially describe the data and to visualize possible starting points for machine learning
- regressions.ipynb contains OLS, lasso, and ridge regressions using a subset of the variables with and without the charter dummy
- regressions_all_vars.ipynb contains regressions using all variables with and without the charter dummy
- primary_regressions.ipynb contains regresssions for only primary schools
- middle_regressions.ipynb contains regresssions for only middle schools
- secondary_regressions.ipynb contains regresssions for only secondary schools
- clustering.ipynb contains the hierarchical and kmeans clustering with various variables 
- preprocessing.py handles the data cleaning of the original dataset, including features such as fixed effects and the calculation of averages and percents
- /yearly_data is a directory containing the year-by-year datasets for the data
- /combined_data is a directory containing the data of all schools for every year in the study with school test scores
