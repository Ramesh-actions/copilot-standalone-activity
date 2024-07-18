import requests
import csv
import os
from datetime import datetime

# Global constants
ENTERPRISE_SLUG = os.getenv('INPUT_ENT_NAME')
TEAM_NAME_FILTER = os.getenv('INPUT_TEAM_NAME')
AUTH_TOKEN = os.getenv('INPUT_GITHUB_TOKEN')

if not AUTH_TOKEN:
    raise ValueError("The INPUT_GITHUB_TOKEN environment variable is not set.")

# Debug statements
print(f"ENTERPRISE_SLUG: {ENTERPRISE_SLUG}")
print(f"TEAM_NAME_FILTER: {TEAM_NAME_FILTER}")
print(f"AUTH_TOKEN: {AUTH_TOKEN[:5]}...")  # Print only the first 5 characters for security

# API version header
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_teams():
    url = f"https://api.github.com/enterprises/{ENTERPRISE_SLUG}/teams"
    teams = []
    
    while url:
        response = requests.get(url, headers=headers)
        print(f"Request URL: {url}, Status Code: {response.status_code}")  # Debug statement
        if response.status_code == 200:
            data = response.json()
            teams.extend(data)
            url = response.links.get('next', {}).get('url')
        else:
            raise Exception(f"Error: Received response code {response.status_code}")
    
    return teams

def get_team_memberships(team_slug):
    url = f"https://api.github.com/enterprises/{ENTERPRISE_SLUG}/teams/{team_slug}/memberships"
    members = []
    
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            members.extend(data)
            url = response.links.get('next', {}).get('url')
        else:
            raise Exception(f"Error: Received response code {response.status_code}")
    
    return members

def get_copilot_billing_seats():
    url = f"https://api.github.com/enterprises/{ENTERPRISE_SLUG}/copilot/billing/seats"
    seats = []
    
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            seats.extend(data['seats'])
            url = response.links.get('next', {}).get('url')
        else:
            raise Exception(f"Error: Received response code {response.status_code}")
    
    return seats

def main():
    # Get all teams if no specific team filter is provided, otherwise get only the specific team
    if TEAM_NAME_FILTER:
        teams = [team for team in get_teams() if team.get('name') == TEAM_NAME_FILTER]
    else:
        teams = get_teams()

    if not teams:
        print(f"No teams found for the filter '{TEAM_NAME_FILTER}'")
        return

    print(f"Fetched {len(teams)} teams")

    copilot_seats = get_copilot_billing_seats()
    print(f"Fetched {len(copilot_seats)} Copilot seats")

    output_data = []

    for team in teams:
        team_slug = team['slug']
        members = get_team_memberships(team_slug)
        print(f"Team '{team['name']}' has {len(members)} members")

        for member in members:
            if member['type'] == 'User':
                username = member['login']
                copilot_info = next((seat for seat in copilot_seats if seat.get('assignee', {}).get('login') == username), None)
                
                if copilot_info:
                    output_data.append({
                        'enterprise_name': ENTERPRISE_SLUG,
                        'team_name': team['name'],
                        'user_name': username,
                        'copilot_activity': copilot_info['last_activity_at'],
                        'last_active_editor': copilot_info['last_activity_editor'],
                        'status': 'active' if copilot_info['last_activity_editor'] else 'inactive'
                    })
    
    if not output_data:
        print("No data to write to CSV")
    else:
        # Specify the CSV file name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_file_name = f"teams_{timestamp}.csv"

        # Define the fieldnames based on the dictionary keys
        fieldnames = ['enterprise_name', 'team_name', 'user_name', 'copilot_activity', 'last_active_editor', 'status']

        # Open the file in write mode and create a csv.DictWriter object
        with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write the header
            writer.writeheader()

            # Write the data rows
            for row in output_data:
                writer.writerow(row)

        print(f"Data written to {csv_file_name}")

if __name__ == "__main__":
    main()
