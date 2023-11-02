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
    for smell in smell_list:
        #calc significative sample
        sample_size = sample_define(smell_count.loc[smell]['project_name'])
        #get sample
        sample = df[df['smell_name'] == smell]
        if sample_size < len(sample):
            sample = sample.sample(n=sample_size)
        print("smell: ", smell,"| whole size:", smell_count.loc[smell]['project_name'], "| sample size: ", sample_size,"| selected size:",len(sample))
        #delete projects used for the sample
        df = df[~df['project_name'].isin(sample['project_name'])]
        #save sample
        final_df = pd.concat([final_df, sample])
    final_df.to_csv(os.path.join(path, "merged_sample.csv"), index=False, header=True)


def cyclic_sampling(path):
    df = pd.read_csv(os.path.join(path, "eligible_projects.csv"))
    df_log = pd.read_csv(os.path.join(path,"merged_sample.csv"))
    # count occurrences for each smell
    smell_count = df.groupby(['smell_name']).count().sort_values(by=['project_name'], ascending=True)
    # get first column
    smell_list = smell_count.iloc[:, 0]
    # get smell list
    smell_list = smell_list.index.tolist()
    final_df = pd.DataFrame(columns=['filename', 'smell_name', 'line', 'message', 'github_repo'])
    for smell in smell_list:
        already_used = df_log[df_log['smell_name'] == smell]
        df_app = df[~df['project_name'].isin(already_used['project_name'])]
        # calc significative sample
        sample_size = sample_define(smell_count.loc[smell]['project_name'])
        # get sample
        sample = df_app[df_app['smell_name'] == smell]
        if sample_size < len(sample):
            sample = sample.sample(n=sample_size)
        print("smell: ", smell, "| whole size:", smell_count.loc[smell]['project_name'], "| sample size: ", sample_size,
              "| selected size:", len(sample))
        # delete projects used for the sample
        df = df[~df['project_name'].isin(sample['project_name'])]
        # save sample
        final_df = pd.concat([final_df, sample])
    final_df.to_csv(os.path.join(path, "final_sample2.csv"), index=False, header=True)

def merge_cycles(path):
    df1 = pd.read_csv(os.path.join(path, "merged_sample.csv"))
    df2 = pd.read_csv(os.path.join(path, "final_sample2.csv"))
    df = pd.concat([df1,df2])
    df.to_csv(os.path.join(path, "merged_sample.csv"), index=False, header=True)

def report_actual_execution(path):
    out = pd.DataFrame(columns=['project_name', 'smell_name', 'line', 'message', 'github_repo','status'])
    in_exec = pd.read_csv(os.path.join(path, "../../log/execution_log.csv"))
    in_sample = pd.read_csv(os.path.join(path, "merged_sample.csv"))
    for index,row in in_sample.iterrows():
        sample_filename = row['project_name'].replace("\\","$")
        found = False
        for index, in_row in in_exec.iterrows():

            if sample_filename in in_row['project_name']:
                found = True
                #get row from in_exec
                project_name = in_row['project_name'].split("\\")[2]

                if row['smell_name'] in in_row['filename']:
                    #add row to out with status = done
                    out = out._append({'project_name': sample_filename, 'smell_name': row['smell_name'],
                                      'line': row['line'], 'message': row['message'], 'github_repo': row['github_repo'],
                                      'status': 'done'}, ignore_index=True)
                else:
                    #add row to out with status = not done
                    out = out._append({'project_name': sample_filename, 'smell_name': row['smell_name'],
                                      'line': row['line'], 'message': row['message'], 'github_repo': row['github_repo'],
                                      'status': 'conflict'}, ignore_index=True)
    #save output
        if not found:
            out = out._append({'project_name': sample_filename, 'smell_name': row['smell_name'],
                               'line': row['line'], 'message': row['message'], 'github_repo': row['github_repo'],
                               'status': 'todo'}, ignore_index=True)
    out.to_csv(os.path.join(path, "diff_log.csv"), index=False, header=True)



def overview_cycling_sampling(path):
    overview_df = pd.read_csv(os.path.join(path, "overview_output.csv"))
    if not os.path.exists(os.path.join(path, "merged_sample.csv")):
        sample_df = pd.DataFrame(columns=['filename', 'smell_name', 'line', 'message', 'github_repo','iteration'])
    else:
        sample_df = pd.read_csv(os.path.join(path, "merged_sample.csv"))
    #get smell count
    smell_count_list = overview_df.groupby(['smell_name']).count().sort_values(by=['filename'], ascending=True)
    #get smell list ordered by count
    smell_list = smell_count_list.index.tolist()
    completed = True
    iteration = 0
    while completed:
        completed = False
        iteration = iteration + 1
        candidate_set = overview_df[['smell_name', 'github_repo']].drop_duplicates()
        for smell in smell_list:
            smell_already_added = sample_df[sample_df['smell_name'] == smell]
            smell_candidate_set = candidate_set[candidate_set['smell_name'] == smell]
            sample_size_required = sample_define(len(smell_candidate_set))
            #disallow repetition of projects for the same smell
            smell_candidate_set = smell_candidate_set[~smell_candidate_set['github_repo'].isin(smell_already_added['github_repo'])]


            if len(smell_already_added) >= sample_size_required:
                continue
            else:
                completed = True
                #get sample
                if sample_size_required-len(smell_already_added) > len(smell_candidate_set):
                    sample = smell_candidate_set
                else:
                    sample = smell_candidate_set.sample(n=sample_size_required-len(smell_already_added))
                #add iteration column
                sample['iteration'] = iteration
                #add sample to sample_df
                sample_df = pd.concat([sample_df,sample])
                #delete sample from overview_df
                overview_df = overview_df[~overview_df['github_repo'].isin(sample['github_repo'])]
                #delete candidate_set from candidate_set
                candidate_set = candidate_set[~candidate_set['github_repo'].isin(sample['github_repo'])]

    sample_df.to_csv(os.path.join(path, "merged_sample.csv"), index=False, header=True)

def sample_report(path):
    all_projects = pd.read_csv(os.path.join(path, "eligible_projects.csv"))
    all_projects.drop_duplicates(inplace=True)
    all_projects.to_csv(os.path.join(path, "eligible_projects.csv"), index=False, header=True)
    sample_df = pd.DataFrame(columns=['smell_name', 'sample_size'])
    smell_list = all_projects['smell_name'].unique().tolist()
    for smell in smell_list:
        smell_projects = all_projects[all_projects['smell_name'] == smell]
        sample_size = sample_define(len(smell_projects))
        #add sample to sample_df not using append
        sample_df = pd.concat([sample_df, pd.DataFrame({'smell_name': smell, 'sample_size': sample_size}, index=[0])])
        sample_df.to_csv(os.path.join(path, "sample_report.csv"), index=False, header=True)

def check_sample(path):
    smell_report = pd.read_csv(os.path.join(path, "sample_report.csv"))
    output = pd.read_csv(os.path.join(path, "merged_sample.csv"))
    #delete header
    output = output[output['filename'] != 'filename']
    smell_report = smell_report[smell_report['smell_name'] != 'smell_name']
    smell_list = smell_report['smell_name'].unique().tolist()

    for smell in smell_list:
        smell_projects = output[output['smell_name'] == smell]
        if len(smell_projects) != smell_report[smell_report['smell_name'] == smell]['sample_size'].values[0]:
            print(smell, " not ok")
            print("expected: ", smell_report[smell_report['smell_name'] == smell]['sample_size'].values[0])
            print("actual: ", len(smell_projects))
            return False
        else:
            print(smell, " ok")
    return True

def check_with_execution_log(path):
    execution_log = pd.read_csv(os.path.join(path, "../../log/execution_log.csv"))
    sample = pd.read_csv(os.path.join(path, "merged_sample.csv"))
    diff = pd.DataFrame(columns=['project_name', 'filename','status','link','sample'])
    for index_s, row_exec in execution_log.iterrows():
        found = False
        for index, row in sample.iterrows():
            project_name = row['github_repo'].replace("\\", "$")
            smell_name = row['smell_name']
            if project_name in row_exec['project_name'] and smell_name in row_exec['filename']:
                found = True
                diff = pd.concat([diff, pd.DataFrame({'project_name': row_exec['project_name'],
                                                      'filename': row_exec['filename'],
                                                      'status': row_exec['status'],
                                                      'link': row_exec['link'],
                                                      'sample': 'included'}, index=[0])])
                break
        if not found:

            #concat row to diff
            diff = pd.concat([diff, pd.DataFrame({'project_name': row_exec['project_name'],
                                                  'filename': row_exec['filename'],
                                                  'status': row_exec['status'],
                                                  'link': row_exec['link'],
                                                  'sample': 'not included'}, index=[0])])
    diff.to_csv(os.path.join(path, "diff_log.csv"), index=False, header=True)


def extract_issue_sample(path):
    sample = pd.read_csv(os.path.join(path, "merged_sample.csv"))
    overview = pd.read_csv(os.path.join(path, "overview_output.csv"))
    issues = pd.DataFrame(columns=['filename', 'function_name','smell_name', 'line', 'github_repo'])
    #get smell list
    smell_list = overview['smell_name'].unique().tolist()
    #get smell count
    for smell in smell_list:
        smell_sample = sample[sample['smell_name'] == smell]
        for index,row in smell_sample.iterrows():
            overview_row = overview[(overview['github_repo'] == row['github_repo']) & (overview['smell_name'] == smell)]
            if len(overview_row) > 1:
                overview_row = overview_row.sample(n=1)
            if len(overview_row) > 0:
                issues = pd.concat([issues, pd.DataFrame({'filename': overview_row['filename'].values[0],
                                                      'function_name': overview_row['function_name'].values[0],
                                                      'smell_name': smell,
                                                      'line': overview_row['line'].values[0],
                                                      'github_repo': overview_row['github_repo'].values[0]}, index=[0])])
    issues.to_csv(os.path.join(path, "issue_sample.csv"), index=False, header=True)


def merge_execution_log(path):
    overview_issue = pd.read_csv(os.path.join(path, "issue_sample.csv"))
    execution_log = pd.read_csv(os.path.join(path, "../../log/execution_log.csv"))
    for index, row in execution_log.iterrows():
        for index_i,row_issue in overview_issue.iterrows():
            if row['project_name'] in row_issue['github_repo'] and row['filename'] in row_issue['smell_name']:
                overview_issue.loc[index_i,'status'] = row['status']
                overview_issue.loc[index_i, 'link'] = row['link']
                overview_issue.loc[index_i, 'message'] = row['message']
                overview_issue.loc[index_i, 'line'] = row['line']
                overview_issue.loc[index_i, 'function_name'] = row['function_name']
                overview_issue.loc[index_i, 'filename'] = row['filename']
                overview_issue.loc[index_i, 'project_name'] = row['project_name']
                overview_issue.loc[index_i,'github_repo'] = row['github_repo']
                break
    overview_issue.to_csv(os.path.join(path, "issue_sample.csv"), index=False, header=True)

def register_log(path):
    overview_issue = pd.read_csv(os.path.join(path, "issue_sample.csv"))
    execution_log = pd.read_csv(os.path.join(path, "../../log/execution_log.csv"))
    log_issue = pd.read_csv(os.path.join(path, "issue_log.csv"))
    overview_issue['status'] = 'not sent'
    overview_issue['link'] = ''

    for index, row in execution_log.iterrows():
        ex_filename = row['filename']
        ex_project_name = row['project_name'].split("\\")[2].replace("$", "\\")
        for index_i,row_issue in log_issue.iterrows():
            if ex_project_name in row_issue['github_repo'] and row_issue['smell_name'] in ex_filename:
                log_issue.loc[index_i,'status'] = row['status']
                log_issue.loc[index_i, 'link'] = row['link']


    log_issue.to_csv(os.path.join(path, "issue_log.csv"), index=False, header=True)

def main():
    path = "C:\\Users\\Gilberto\\Documents\\Github\\IssueSmellTracker\\samples_overview\\eng"

    el= get_all_eligible_projects(path)
    el.to_csv(os.path.join(path, "eligible_projects.csv"), index=False, mode='a', header=True)
    register_log(path)

if __name__ == '__main__':
    main()

