from random import sample

import pandas as pd
import os


def get_eligible_projects(path,smell):
    df = pd.read_csv(os.path.join(path, "smell_per_project.csv"))

    # Extract the relevant columns and escape the project_name column
    df = df[['project_name', smell]].replace({'\$': '\\\\'}, regex=True)

    # Filter eligible projects
    eligible_projects = df[df[smell] > 0]

    # Assign the 'smell_name' column without the need for a loop
    eligible_projects.loc[:, 'smell_name'] = smell

    # Select the desired columns
    eligible_projects = eligible_projects[['project_name', 'smell_name']]

    return eligible_projects

def get_all_eligible_projects(path):
    df = pd.read_csv(os.path.join(path,"smell_per_project.csv"))
    #get smell_list
    smell_list = df.columns.tolist()
    smell_list.remove('project_name')
    #format project_name in recording table
    df['project_name'] = df['project_name'].str.replace("$", "\\")
    #get projects that can be used as sample of the selected smell
    eligible_projects = pd.DataFrame(columns=['project_name',"smell_name"])
    for smell in smell_list:
        eligible_projects = pd.concat([eligible_projects, get_eligible_projects(path,smell)])
    return eligible_projects

def sample_define(population_size):
    if population_size <30:
        return population_size
    else:
        margin_of_error = 0.05

        # Z-score for a 95% confidence level (standard value is 1.96)
        confidence_level = 0.95
        z_score = 1.96

        # Estimated proportion of the population (you can adjust this)
        p = 0.5  # For maximum variability, you can use 0.5

        # Calculate the sample size
        sample_size = (z_score ** 2 * population_size * p * (1 - p)) / (
                (population_size - 1) * (margin_of_error ** 2) + z_score ** 2 * p * (1 - p)
        )
        return int(sample_size)

def sample_extraction(path):
    df = pd.read_csv(os.path.join(path,"eligible_projects.csv"))
    #count occurrences for each smell
    smell_count = df.groupby(['smell_name']).count().sort_values(by=['project_name'], ascending=True)
    #get first column
    smell_list = smell_count.iloc[:,0]
    #get smell list
    smell_list = smell_list.index.tolist()
    final_df = pd.DataFrame(columns=['filename', 'smell_name', 'line', 'message', 'github_repo'])
    print(smell_list)
    for smell in smell_list:
        #calc significative sample
        print("smell: ", smell, "sample size: ", smell_count.loc[smell]['project_name'])
        sample_size = sample_define(smell_count.loc[smell]['project_name'])
        #get sample
        sample = df[df['smell_name'] == smell]
        if sample_size < len(sample):
            sample = sample.sample(n=sample_size)
        #delete projects used for the sample
        df = df[~df['project_name'].isin(sample['project_name'])]
        #save sample
        final_df = pd.concat([final_df, sample])
    final_df.to_csv(os.path.join(path, "final_sample.csv"), index=False, header=True)


def main():
    path = "C:\\Users\\Gilberto\\Documents\\Github\\IssueSmellTracker\\samples_overview\\no_eng"

    el= get_all_eligible_projects(path)
    el.to_csv(os.path.join(path, "eligible_projects.csv"), index=False, mode='a', header=True)
    sample_extraction(path)

if __name__ == '__main__':
    main()

