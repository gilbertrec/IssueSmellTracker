import pandas
import pandas as pd
import time
import requests
from permalink_extractor import get_last_commit_id


def create_github_issue(repo, title, body, token):
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print("Issue created successfully.")
    elif response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 1))
        print(f"Rate limited. Retrying after {retry_after} seconds.")
        time.sleep(retry_after)
        create_github_issue(repo, title, body, token)  # Retry the request
    elif response.status_code == 403:
        print(" Secondary Rate limited. Try again later.")
        retry_after = int(response.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        create_github_issue(repo, title, body, token)  # Retry the request
    else:
        print("Failed to create issue. Error:", response.text)

def create_message(row,otherfiles):
    smell_table = pd.read_csv("smell_table.csv")
    with open("templates/issue_title.txt", "r") as f:
        title = f.read()

    smell_ref = smell_table[smell_table['smell_id'] == row['smell_name']]

    title = title.replace("$smell_name$", smell_ref['smell_name'].iloc[0])
    title = title.replace("$filename$", row['filename'].split("\\")[-1])
    title = title.replace("$line_number$", str(row['line']))

    message = open("templates/issue_body_v3.txt", "r").read()
    code_link = get_code_snippet_reference(row)

    message = message.replace("$filename$", row['filename'].split("\\")[-1])
    message = message.replace("$filepath$", code_link.replace("\\","/"))
    message = message.replace("$github_repo$", row['github_repo'].replace("\\","/"))
    message = message.replace("$line_start$", str(row['line']-10))
    message = message.replace("$line_end$", str(row['line']+10))
    message = message.replace("$smell_name$", smell_ref['smell_name'].iloc[0])
    message = message.replace("$smell_description$", smell_ref['smell_Context'].iloc[0])
    message = message.replace("$smell_problem$", smell_ref['smell_Problem'].iloc[0])
    message = message.replace("$smell_solution$", smell_ref['smell_Solution'].iloc[0])
    message = message.replace("$smell_impact$", smell_ref['smell_Impact'].iloc[0])
    other_file_message = ""
    last_commit_id = get_last_commit_id(row['github_repo'].split("/")[0],row['github_repo'],code_link.replace("\\","/"))
    print("Last commit id:",last_commit_id)
    message = message.replace("$master$", get_last_commit_id(row['github_repo'].split("\\")[0],row['github_repo'].split("\\")[1],code_link.replace("\\","/")) )

    for index,file in otherfiles.iterrows():
        if index < 5 and file['filename'] != row['filename']:
            github_Repo = "https://github.com/$github_repo$/blob/master$filepath$#L$line_start$-L$line_end$"
            github_Repo = github_Repo.replace("$github_repo$", file['github_repo'].replace("\\","/"))
            github_Repo = github_Repo.replace("$filepath$", get_code_snippet_reference(file).replace("\\","/"))
            github_Repo = github_Repo.replace("$line_start$", str(file['line'] - 5))
            github_Repo = github_Repo.replace("$line_end$", str(file['line'] + 5))
            other_file_message += f"File: {github_Repo} Line: {file['line']}\n"

    message = message.replace("$other_files_list$", other_file_message)
    return title,message

def get_code_snippet_reference(row):
    #get right part of the filename starting from project name
    filename = row['filename']
    filename = filename.split(row['github_repo'].replace("\\","$"))[1]
    return filename


def send_issue_report(path):
    repo_report = pandas.read_csv(path)

    if repo_report.empty:
        return
    smell_file = None
    for index,row in repo_report.iterrows():
        other_files = []

        if index > 0:
            other_files.append(row)
        else: smell_file = row
    # create issue message for the report
    title, message = create_message(row, repo_report)
    print("Title:", title)
    print("Message:", message)
    # get access token from config file

    access_token = open("config/access_token.txt", "r").read()
    # for debugging
    repo = "gilbertrec/TestRepositoryForCodeSmile2"
    create_github_issue(repo, title, message, access_token)



send_issue_report("F:\\output_for_bot\\allegroaitrains\\columns_and_datatype_not_explicitly_set.csv")


