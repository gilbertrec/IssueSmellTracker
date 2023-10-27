from random import sample

import pandas as pd
import os

def define_samples(path):
    df = pd.read_csv(os.path.join(path,"overview_output.csv"))
    population_sizes = pd.read_csv(os.path.join(path,"smell_overview.csv"))
    #get sample size for each project
    sample_sizes = pd.DataFrame(columns=['smell_name', 'sample_size'])
    for smell in population_sizes['smell_name']:
        population = len(df[df['smell_name'] == smell])
        sample_size = sample_define(population)
        sample_sizes.loc[len(sample_sizes)] = [smell, sample_size]
    return sample_sizes


def get_eligible_projects(path,smell):
    df = pd.read_csv(os.path.join(path,"smell_per_project.csv"))
    df = df[['project_name', smell]]
    #format project_name in recording table
    df['project_name'] = df['project_name'].str.replace("$", "\\")
    #get projects that can be used as sample of the selected smell
    eligible_projects = df[df[smell] > 0]
    #create new column
    eligible_projects['smell_name'] = ""

    eligible_projects = eligible_projects[['project_name', 'smell_name']]
    #add smell name to column

    for index,row in eligible_projects.iterrows():
        row['smell_name'] = smell
        eligible_projects.loc[index] = row
    #remove column of smell

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

def stratify(path):
    sample_sizes = define_samples(path)
    df = pd.read_csv(os.path.join(path,"overview_output.csv"))
    recording_table = pd.read_csv(os.path.join(path,"smell_per_project.csv"))
    #format project_name in recording table
    recording_table['project_name'] = recording_table['project_name'].str.replace("$", "\\")
    used_projects = pd.DataFrame(columns=['project_name'])
    sample_sizes.sort_values(by=['sample_size'], inplace=True, ascending=True)
    output_sample = pd.DataFrame(columns=['filename', 'smell_name', 'line', 'message', 'github_repo'])
    for smell in sample_sizes['smell_name']:
        #get projects that can be used as sample of the selected smell
        eligible_projects = recording_table[recording_table[smell] > 0]
        #delete projects already used
        eligible_projects = eligible_projects[eligible_projects['project_name'].isin(used_projects) == False]
        #check the sum if the sum is less than the sample size, use all projects
        if eligible_projects[smell].sum() < sample_sizes[sample_sizes['smell_name'] == smell]['sample_size'].values[0]:
            sample = df[df['smell_name'] == smell]
            sample.to_csv(os.path.join(path,"sample.csv"), index=False, mode='a', header=False)
        else:
            eligible_projects = eligible_projects[eligible_projects['project_name'].isin(used_projects) == False]
            eligible_projects = eligible_projects['project_name'].unique()
            #get sample from these projects
            sample = df['github_repo'].unique()

            #replace dollar character with backslash
            eligible_projects = [x.replace("$", "\\") for x in eligible_projects]
            for s in sample:
                if s not in eligible_projects:
                    sample = sample[sample != s]
            sample = stratify_sample(sample,sample_sizes[sample_sizes['smell_name'] == smell]['sample_size'].values[0])
            #get rows of the dataframe for the selected smell inthe sample
            sample = df[df['github_repo'].isin(sample)]
            output_sample = pd.concat([output_sample, sample])
            #add projects to used projects
            used_projects = pd.concat([used_projects, pd.DataFrame(sample['github_repo'].unique(), columns=['project_name'])])
        # save sample
        output_sample.to_csv(os.path.join(path, "sample.csv"), index=False, mode='a', header=True)
        unify_samples_per_project(path,output_sample)
    return output_sample

def unify_samples_per_project(path,output_sample):
    #get projects that are in the sample
    projects = output_sample['github_repo'].unique()
    #get rows of the dataframe for the selected projects
    sample = output_sample[output_sample['github_repo'].isin(projects)]
    #save sample
    sample.to_csv(os.path.join(path, "final_sample.csv"), index=False, mode='a', header=True)
    return sample

def stratify_sample(population,sample_size):
    #apply random sampling to population list with sample size
    if len(population) < sample_size:
        return population
    s = sample(population.tolist(), sample_size)
    return s

def sample_define(population):
    if population > 30:
        sample_size = int(population * 0.1)
    else:
        sample_size = population
    return sample_size


def main():
    path = "C:\\Users\\Gilberto\\Documents\\Github\\IssueSmellTracker\\samples_overview\\eng"
    stratify(path)
    el= get_all_eligible_projects(path)
    el.to_csv(os.path.join(path, "eligible_projects.csv"), index=False, mode='a', header=True)

if __name__ == '__main__':
    main()

