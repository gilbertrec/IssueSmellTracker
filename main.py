
import argparse
import os

import pandas as pd
import time

from issue_composer import send_issue_report

def update_issue_log(info_row,link,status,log_path):
    issue_log = pd.read_csv(log_path)
    issue_log.loc[(issue_log["github_repo"] == info_row["github_repo"]) & (issue_log["filename"] == info_row["filename"]),"status"] = status
    issue_log.loc[(issue_log["github_repo"] == info_row["github_repo"]) & (issue_log["filename"] == info_row["filename"]),"link"] = link
    issue_log.to_csv(log_path,index=False)
    return
def send_single_issue(info_row,log_path):
    link = send_issue_report(os.path.join(info_row["github_repo"], info_row["filename"]))
    if link is not None:
        add_log(info_row["github_repo"], info_row["filename"], "completed", link)
        update_issue_log(info_row,link,"completed",log_path)
    elif link == 422:
        add_log(info_row["github_repo"], info_row["filename"], "failed", "Repository Restricted Access")
        update_issue_log(info_row, "Repository Restricted Access", "failed", log_path)
    else:
        add_log(info_row["github_repo"], info_row["filename"], "failed", link)
        update_issue_log(info_row, link, "failed", log_path)
    return link



def send_multiple_issues_on_single_projects(issue_log_path,not_spam=False):
    issue_log = pd.read_csv(issue_log_path,encoding="utf-8")
    issue_log = issue_log[issue_log["status"] == "not sent"]
    if not_spam:
        #for each project, send only one issue
        issue_subset = issue_log.drop_duplicates(subset=["github_repo"])
    else:
        issue_subset = issue_log
    for index, row in issue_subset.iterrows():
        print("Processing:", row["github_repo"], "for smell:", row["filename"])
        link = send_single_issue(row,issue_log_path)
        time.sleep(5)
        print("Processed:", row["github_repo"], "for smell:", row["filename"], "link:", link)

def broadcast_issues(smell_name, projects_path):
    for dir in os.listdir(projects_path):
        # enter a project report
        if os.path.exists(os.path.join(projects_path, dir)):
            print("Processing:", dir, "for smell:", smell_name)
            if smell_name in dir:
                link = send_issue_report(os.path.join(projects_path, smell_name + ".csv"))
                if link is not None:
                    add_log(os.path.join(projects_path, dir), smell_name + ".csv", "completed", link)
                elif link == 422:
                    add_log(os.path.join(projects_path, dir), smell_name + ".csv", "failed", "Repository Restricted Access")
                else:
                    add_log(dir, smell_name + ".csv", "failed", link)

                time.sleep(5)
                print("Processed:", dir, "for smell:", smell_name)
    return

def add_log(github_repo, filename, status, link):
    if not os.path.exists("log/execution_log.csv"):
        create_log_execution_file()
    df = pd.read_csv("log/execution_log.csv")
    df = pd.concat([df, pd.DataFrame([[github_repo, filename, status, link]], columns=df.columns)])
    df.to_csv("log/execution_log.csv", index=False)
    return


def create_log_execution_file():
    if not os.path.exists("log"):
        os.makedirs("./log")
    path = "./log/execution_log.csv"
    df = pd.DataFrame(columns=["github_repo", "filename", "status", "link"])
    df.to_csv(path, index=False)
    return path

def print_log_status():
    if not os.path.exists("log/execution_log.csv"):
        create_log_execution_file()
    df = pd.read_csv("log/execution_log.csv")
    print("Execution log:")
    print("Total execution:", len(df))
    print("Total success:", len(df[df["status"] == "completed"]))
    print("Total failed:", len(df[df["status"] == "failed"]))
    print("Last project:", df["github_repo"].iloc[-1])
    print("Last filename:", df["filename"].iloc[-1])
    print("Last execution status:", df["status"].iloc[-1])
    return

def main(args):
    if args.log:
        print_log_status()
        exit(0)
    if args.input is None:
        print("Please specify input folders")
        exit(0)
    projects_path = args.input
    if args.table:
        send_multiple_issues_on_single_projects(projects_path, not_spam=True)
    else:
        # get smell name and projects path
        if args.smell is None:
            print("Please specify smell name")
            exit(0)
        if args.limit is not None:
            limit = args.limit
        else:
            limit = 0
        smell_name = args.smell

        # broadcast issues
        if args.table:
            send_multiple_issues_on_single_projects(projects_path, not_spam=True)
        else:
            if args.multiple:
                multiple_analysis(smell_name, projects_path, limit)
            else:
                broadcast_issues(smell_name, projects_path)

def multiple_analysis(smell,path,limit=0):
    count = 0
    for dir in os.listdir(path):
        if os.path.exists(os.path.join(path, dir)):
            for file in os.listdir(os.path.join(path, dir)):
                if file.endswith(".csv"):
                    smell_name = file.split(".")[0]
                    if smell in smell_name:
                        broadcast_issues(smell_name, os.path.join(path, dir))
                        count += 1
                        if limit != 0 and count >= limit:
                            print("Limit reached")
                            return
                    else:
                        print("Smell", smell_name, "skipped")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Broadcast issues to GitHub', add_help=False)
    parser.add_argument('--smell', type=str, help='smell name')
    parser.add_argument('--input', type=str, help='input folder')
    parser.add_argument('--log', help='log file', action='store_true')
    parser.add_argument('--help', help='help', action='store_true')
    parser.add_argument('--multiple', help='broadcast issues of multiple projects', action='store_true')
    parser.add_argument('--table', help='use csv table to send multiple issues (csv path as input parameter)', action='store_true')
    parser.add_argument('--limit', type=int, help='set a limit of number of issues to send')
    args = parser.parse_args()
    if args.help:
        print("Broadcast issues of the results of CodeSmile analysis to GitHub!")
        print("Usage: python3 main.py --smell <smell_name> --input <input_folder>")
        print("Options:")
        print("--log : print log status")
        print("--help : print help")
        print('--table: use csv table to send multiple issues (csv path as input parameter)')
        print("--multiple: broadcast issues of multiple projects")
        print("--limit: set a limit of number of issues to send")
        exit(0)
    else:
        main(args)