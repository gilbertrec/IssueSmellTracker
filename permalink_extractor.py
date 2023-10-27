import requests
import time
import random
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
    elif response.status_code == 403:
        print("Secondary Rate limited to get commit_id. Try again later.")
        retry_after = int(response.headers.get("Retry-After", 60))
        random_time = random.randint(1, 10)
        print(f"Retrying after {random_time*retry_after} seconds.")
        time.sleep(random_time*retry_after)
        return get_last_commit_id(owner, repo, path)

    return None