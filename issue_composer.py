import pandas
import pandas as pd

from permalink_extractor import get_last_commit_id
from main import create_github_issue


def create_message(row,otherfiles):
    smell_table = pd.read_csv("smell_table.csv")
    with open("templates/issue_title.txt", "r") as f:
        title = f.read()

    smell_ref = smell_table[smell_table['smell_id'] == row['smell_name']]

    title = title.replace("$smell_name$", smell_ref['smell_name'].iloc[0])
    title = title.replace("$filename$", row['filename'].split("\\")[-1])
    title = title.replace("$line_number$", str(row['line']))

    message = open("templates/issue_body.txt", "r").read()
    code_link = get_code_snippet_reference(row)

    message = message.replace("$filename$", row['filename'].split("\\")[-1])
    message = message.replace("$filepath$", code_link.replace("\\","/"))
    message = message.replace("$github_repo$", row['github_repo'].replace("\\","/"))
    message = message.replace("$line_start$", str(row['line']-5))
    message = message.replace("$line_end$", str(row['line']+5))
    message = message.replace("$smell_name$", smell_ref['smell_name'].iloc[0])
    message = message.replace("$smell_description$", smell_ref['smell_Problem'].iloc[0])

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


def get_repo_smell_report(path):
    repo_report = pandas.read_csv(path)

    if repo_report.empty:
        return
    smell_file = None
    for index,row in repo_report.iterrows():
        other_files = []

        if (index > 0):
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
    exit()
    print("Github Repo:", repo)
    filename = row['filename']
    repo_path = repo



get_repo_smell_report("F:\\output_for_bot\\allegroaitrains\\columns_and_datatype_not_explicitly_set.csv")


