import requests

def get_last_commit_id(owner, repo, path):
    # API endpoint to fetch the commits for a specific file
    api_url = f'https://api.github.com/repos/{owner}/{repo}/commits?path={path}'

    # Sending GET request to the GitHub API
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()

        if len(data) > 0:
            last_commit_id = data[0]['sha']

            return last_commit_id


    return None