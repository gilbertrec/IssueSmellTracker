# This is a sample Python script.
import requests
import time


def create_github_issue(repo, title, body, token):
    url = f"https://api.github.com/repos/{repo}/issues"
    print("URL:",url)
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
    elif response.status_code == 429 :
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


# Example usage
repository = "owner/repo"
issue_title = "Example Issue"
issue_body = "This is an example issue created automatically."

#read access token from access_token.txt
with open("config/access_token.txt", "r") as f:
    access_token = f.read()






#def get_repo_smell_report(path):

