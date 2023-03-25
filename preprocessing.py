import pandas as pd
import re

# cleans a name by removing punctuation and numbers and making lowercase 
def clean_name(x):
    return re.sub(r'[^\w\s]|[\d]', '', str(x).lower()).replace(' ', '').strip()

# cleans a value by removing '=' and '"'
def clean_value(x):
    return str(x).replace('=', '').replace('"', '')

# removes quotes from values
def remove_quotes(x):
    return str(x).replace('"', '')

# creates a dummy variable given the name of the column and dataframe
def create_dummy_variables(df, dummy_columns, dummy_names):
    # creates dummy variables
    dummies = pd.get_dummies(df[dummy_columns])

    # creates column names
    dummies.columns = dummy_names
    
    # concatenate dummy variables with original dataframe
    df = pd.concat([df, dummies], axis=1)

    return df

# used to store number of rows in dataframes
count = 0

# loops through each csv for the years when data is available 
for year in [y for y in range(2015, 2023) if y not in [2020, 2021]]:
    # obtains results and filters to school-wide data with certain columns
    df_results = pd.read_csv(f'original_data/results_{year}.csv')

    # retrieves data for all grades and assessments
    if year == 2022:
        df_results = df_results[(df_results['Test Level'] == 'All Assessments') 
                                    & (df_results['Subgroup'] == 'All Students') 
                                    & (df_results['FAY Status'] == 'All')]
    elif year in range (2015, 2019):
        df_results = df_results[(df_results['Test Level'] == 'All') 
                                    & (df_results['Subgroup'] == 'All Students')]
    else:
        df_results = df_results[(df_results['Test Level'] == 'All Assessments') 
                                    & (df_results['Subgroup'] == 'All Students')]

    df_results = df_results[['School Name', 'District Entity ID', 'District Name', 'Percent Passing', 'Subject']]

    # obtains school ids
    df_school_ids = pd.read_csv(f'original_data/school_ids.csv')
    df_school_ids = df_school_ids.drop('State Name', axis=1)
    df_school_ids['Agency ID - NCES Assigned'] = df_school_ids['Agency ID - NCES Assigned'].astype(str)

    # obtains school data
    df_school_data = pd.read_csv(f'original_data/school_data_{year - 1}-{year}.csv')
    df_school_data['Agency ID - NCES Assigned'] = df_school_data['Agency ID - NCES Assigned'].astype(str)

    # merges datasets based on school name and an agency identifier
    if year == 2022:
        df_school_ids = df_school_ids.drop('Agency ID - NCES Assigned', axis=1)
        df_school_data = pd.merge(df_school_data, df_school_ids, 
                                left_on=['School Name', 'Agency Name'], 
                                right_on=['School Name', 'Agency Name'], how='inner')
    else:
        df_school_ids = df_school_ids.drop('Agency Name', axis=1)
        df_school_data = pd.merge(df_school_data, df_school_ids, 
                                left_on=['School Name', 'Agency ID - NCES Assigned'], 
                                right_on=['School Name', 'Agency ID - NCES Assigned'], how='inner')
    df_school_data = df_school_data.drop_duplicates()

    # removes punctuation, white spaces, and converts to lowercase for school names
    df_results['Cleaned School Name'] = df_results['School Name'].apply(clean_name)
    df_school_data['Cleaned School Name'] = df_school_data['School Name'].apply(clean_name)
    df_school_data = df_school_data.drop('School Name', axis=1)

    # merges results with data based on school name, agency name, and angency ID
    if year in range(2015, 2019):
        df_results['Cleaned District Name'] = df_results['District Name'].apply(clean_name)
        df_school_data['Cleaned District Name'] = df_school_data['Agency Name'].apply(clean_name)

        # merges the data frames on the cleaned school names
        df = pd.merge(df_school_data, df_results,
                        left_on=['Cleaned School Name', 'Cleaned District Name'], 
                        right_on=['Cleaned School Name', 'Cleaned District Name'])
        df = df.drop(columns=['Cleaned District Name'])
    else:
        # extracts the numbers in parentheses from 'Agency Name [Public School] {year - 1}-{year}' column
        df_school_data['District Entity ID'] = df_school_data['Agency Name'].str.extract('\((\d+)\)')

        # converts the integer column to string for both data frames and removes copy of 'School Name'
        df_results['District Entity ID'] = df_results['District Entity ID'].astype(str)
        df_school_data['District Entity ID'] = df_school_data['District Entity ID'].astype(str)

        # merges the data frames on the cleaned school names
        df = pd.merge(df_school_data, df_results,
                        how='inner',
                        left_on=['Cleaned School Name', 'District Entity ID'], 
                        right_on=['Cleaned School Name', 'District Entity ID'])

    # drops the cleaned school names column
    df = df.drop(columns=['Cleaned School Name'])
    df = df.drop_duplicates()

    # saves combined data frame as a CSV in data folder
    df.to_csv(f'yearly_data/{year}.csv', index=False)

    # converts percents to numbers
    df['Percent Passing'] = pd.to_numeric(df['Percent Passing'], errors='coerce')

    # groups the dataframe by school name
    grouped = df.groupby('School Name')

    # calculates the average percent proficient for each school
    averages = grouped['Percent Passing'].mean()

    # creates a new dataframe to store the results
    df_combined = pd.DataFrame({'School Name': averages.index, 'Average Percent Passing': averages.values})
    df_combined = pd.merge(df, df_combined,
                        how='inner',
                        left_on='School Name',
                        right_on='School Name')
    df_combined = df_combined.drop(['Subject', 'Percent Passing', 'State Name'], axis=1)
    df_combined = df_combined.drop_duplicates(subset=['School ID - NCES Assigned'], inplace=False)

    # handles missing values
    df_combined = df_combined.applymap(clean_value)
    df_combined = df_combined.replace(['-', '†', '', 'Nan', '–', '=0', 'nan', '‡'], pd.NaT, inplace=False)

    # adds year column
    df_combined['Year'] = year

    # removes the teacher and student variables due to missing values
    df_combined = df_combined.drop(['Full-Time Equivalent (FTE) Teachers', 'Pupil/Teacher Ratio'], axis=1)  

    # # finds means for numeric columns and uses to fill in missing values
    # numeric_cols = df_combined.select_dtypes(include=['float', 'int']).columns
    # means = df_combined[numeric_cols].mean()
    # df_combined[numeric_cols] = df_combined[numeric_cols].fillna(means)

    # create dummy variables for charter schools
    df_combined['Charter School Dummy'] = (df_combined['Charter School'] == '1-Yes').astype(int)

    # converts number of each gender and race to proportions of total students for the school
    demographics = ["Male Students", "Female Students", "American Indian/Alaska Native Students", 
                    "Asian or Asian/Pacific Islander Students", "Hispanic Students", 
                    "Black or African American Students", "White Students", 
                    "Nat. Hawaiian or Other Pacific Isl. Students", "Two or More Races Students", 
                    "Free and Reduced Lunch Students"]
    percentage_columns = [d + " Percentage" for d in demographics]
    for index, row in df_combined.iterrows():
        total_students = pd.to_numeric(row["Total Students All Grades (Excludes AE)"], errors='coerce')
        for d, p in zip(demographics, percentage_columns):
            count = pd.to_numeric(row[d], errors='coerce')
            if not pd.isna(count) and total_students != 0 and not pd.isna(total_students):
                df_combined.at[index, p] = count / total_students
            else:
                df_combined.at[index, p] = pd.NaT

    # create dummy variables for school level
    df_combined['School Level'] = df_combined['School Level'].replace(['Not Applicable', 'Not Reported'], 'Other')
    school_level = ['School Level: Primary', 'School Level: Middle', 'School Level: High',
                    'School Level: Other']
    df_combined = create_dummy_variables(df_combined, ['School Level'], school_level)

    # creates dummy variables for county 
    county_names = ['Apache County', 'Cochise County', 'Coconino County', 'Gila County',
                    'Graham County', 'Greenlee County', 'La Paz County', 'Maricopa County',
                    'Mohave County', 'Navajo County', 'Pima County', 'Pinal County', 
                    'Santa Cruz County', 'Yavapai County', 'Yuma County']
    df_combined = create_dummy_variables(df_combined, ['County Name'], county_names)

    # creates dummy variables for congressional districts
    districts = ['0403', '0401', '0406', '0407', '0404', '0402', '0405', '0409', '0408']
    df_combined = create_dummy_variables(df_combined, ['Congressional Code'], districts)

    # # adds year to the end of time-dependent variables
    # cols_to_keep = ['Agency Name', 'Agency ID - NCES Assigned', 'County Name',
    #             'County Number', 'Charter School', 'Title I School Status',
    #             'Congressional Code', 'National School Lunch Program', 'School Level',
    #             'School Name', 'District Entity ID', 'District Name', 'Charter School Dummy',
    #             'School Level: Primary', 'School Level: Middle', 'School Level: High', 
    #             'School Level: Other', 'Apache County', 'Cochise County', 'Coconino County', 
    #             'Gila County', 'Graham County', 'Greenlee County', 'La Paz County', 'Maricopa County',
    #             'Mohave County', 'Navajo County', 'Pima County', 'Pinal County', 
    #             'Santa Cruz County', 'Yavapai County', 'Yuma County', 'School ID - NCES Assigned',
    #             '0403', '0401', '0406', '0407', '0404', '0402', '0405', '0409', '0408']
    # rename_dict = {}
    # for col in df_combined.columns:
    #     if col not in cols_to_keep:
    #         rename_dict[col] = f"{col} {year}"
    #     else:
    #         rename_dict[col] = col
    # df_combined = df_combined.rename(rename_dict, axis=1)

    # writes the results to a new CSV file
    df_combined.to_csv(f'yearly_data/combined_{year}.csv', index=False)

    # updates count
    count += df_combined.shape[0]
    print(count)

# loads all the combined datasets
df1 = pd.read_csv('yearly_data/combined_2015.csv')
df2 = pd.read_csv('yearly_data/combined_2016.csv')
df3 = pd.read_csv('yearly_data/combined_2017.csv')
df4 = pd.read_csv('yearly_data/combined_2018.csv')
df5 = pd.read_csv('yearly_data/combined_2019.csv')
df6 = pd.read_csv('yearly_data/combined_2022.csv')

# combines all the dataframes
df_merged = pd.concat([df1, df2, df3, df4, df5, df6])
df_merged = df_merged.reindex(columns=['School Name'] + list(df_merged.columns.drop('School Name')))
df_merged = df_merged.sort_values('School Name')

# creates dummy variables for national school lunch program offerings
df_merged = df_merged.dropna(subset=['National School Lunch Program'])
offerings = ['NSLP: No', 'NSLP: Yes, without Provision or CEO', 'NSLP: Yes, under CEO', 'NSLP: Yes, under Provision 2',
             'NSLP: Yes, under Provision 3']
df_merged = create_dummy_variables(df_merged, ['National School Lunch Program'], offerings)

# create dummy variables for Title I status
df_merged = df_merged.dropna(subset=['Title I School Status'])
title_status = ['Title I: Targeted Assistance Eligible School - No Program', 'Title I: Targeted Assistance School', 
                'Title I: Schoolwide Eligible - Targeted Assistance Program', 'Title I Schoolwide Eligible School - No Program', 
                'Title I: Schoolwide School', 'Title I: Not a Title I School']
df_merged = create_dummy_variables(df_merged, ['Title I School Status'], title_status)

# create dummy variables for years
dummies = pd.get_dummies(df_merged['Year'])
df_merged = pd.concat([df_merged, dummies], axis=1)

# fills in missing values and sorts by year
df_merged = df_merged.sort_values(by=['School ID - NCES Assigned', 'Year'])
schools = df_merged['School ID - NCES Assigned'].unique()
for school in schools:
    mask = df_merged['School ID - NCES Assigned'] == school
    school_data = df_merged.loc[mask].sort_values(by='Year')
    interpolated_data = school_data.interpolate()
    df_merged.loc[mask] = interpolated_data

# groups by congressional code and fills in missing values with group mean
df_merged = df_merged.groupby('Congressional Code', group_keys=True).apply(lambda group: group.fillna(group.mean(numeric_only=True)))
df_merged.reset_index(drop=True, inplace=True)

# saves the data frame as a CSV
df_merged.to_csv(f'combined_data/combined.csv', index=False)

# # defines the list of dataframes to merge
# dfs_to_merge = [df1, df2, df3, df4, df5]
# cols_to_drop = ['Agency Name', 'Agency ID - NCES Assigned', 'County Name',
#                 'County Number', 'Charter School', 'Title I School Status',
#                 'Congressional Code', 'National School Lunch Program', 'School Level',
#                 'School Name', 'District Entity ID', 'District Name', 'Charter School Dummy',
#                 'School Level: Primary', 'School Level: Middle', 'School Level: High', 
#                 'School Level: Other', 'Apache County', 'Cochise County', 'Coconino County', 
#                 'Gila County', 'Graham County', 'Greenlee County', 'La Paz County', 'Maricopa County',
#                 'Mohave County', 'Navajo County', 'Pima County', 'Pinal County', 
#                 'Santa Cruz County', 'Yavapai County', 'Yuma County', '0403', '0401', '0406', 
#                 '0407', '0404', '0402', '0405', '0409', '0408']
# dfs_to_merge = list(map(lambda df: df.drop(cols_to_drop, axis=1), dfs_to_merge))
# dfs_to_merge.append(df6)

# # merges all the dataframes
# df_merged = reduce(lambda left, right: pd.merge(left, right, how='inner', left_on='School ID - NCES Assigned', right_on='School ID - NCES Assigned'), dfs_to_merge)

# # saves the data frame as a CSV
# df_merged = df_merged.reindex(columns=['School Name'] + list(df_merged.columns.drop('School Name')))
# df_merged = df_merged.drop_duplicates(subset=['School ID - NCES Assigned'], inplace=False)
# df_merged.to_csv(f'combined_data/combined.csv', index=False)

print(df_merged.shape[0])