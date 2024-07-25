#!/usr/bin/env python

import os
import requests
import json
import datetime
from datetime import datetime, timezone
import logging

# Constants
GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'
GITHUB_API_URL = 'https://api.github.com'
ENTERPRISE_SLUG = 'canarys'
PERSONAL_ACCESS_TOKEN = os.environ.get('GH_ADMIN_TOKEN')
ORGANIZATIONS_PER_PAGE = 100  # Adjust this number if needed
active_days = 15

# Logging Configuration
logging.basicConfig(filename='github_api.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Headers for the request
headers = {
    'Authorization': f'bearer {PERSONAL_ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

def fetch_organizations(cursor=None):
    # GraphQL query with pagination
    query = f'''
    {{
      enterprise(slug: "{ENTERPRISE_SLUG}") {{
        organizations(first: {ORGANIZATIONS_PER_PAGE}{', after: "' + cursor + '"' if cursor else ''}) {{
          edges {{
            node {{
              name
              login
            }}
          }}
          pageInfo {{
            endCursor
            hasNextPage
          }}
        }}
      }}
    }}
    '''
    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Query failed with status code {response.status_code}. Response: {response.text}")

def fetch_copilot_seats(org_login,page,all_seats=None):
    logging.info(f"Fetching Copilot seats for organization: {org_login}, page: {page}")
    per_page = 100  # Maximum allowed by GitHub API
    if all_seats is None:
        all_seats = []
    #all_seats = []
    url = f'{GITHUB_API_URL}/orgs/{org_login}/copilot/billing/seats?page={page}&per_page={per_page}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data=response.json()  
        if data['seats']:
            logging.info(f"Seats found for {org_login}, page: {page}")
            all_seats.extend(data['seats'])
            page += 1
            fetch_copilot_seats(org_login,page,all_seats)
            return all_seats 
        else:
            logging.info(f"No more seats found for {org_login} in page: {page}")
        
    else:
       logging.error(f"Failed to fetch Copilot seats for {org_login}, page: {page}. Status code: {response.status_code}, Response: {response.text}")

def main():
    all_organizations = []
    page=1
    cursor = None
    has_next_page = True
    current_date = datetime.now(timezone.utc)
    with open('copilot.csv', 'a') as f:
        f.write('Organization,User,Last Activity,Last Activity Editor,Status\n')
        while has_next_page:
            result = fetch_organizations(cursor)
            if result is None:
                logging.error("Failed to fetch organizations. Exiting.")
                return
            organizations = result['data']['enterprise']['organizations']
            all_organizations.extend(edge['node'] for edge in organizations['edges'])
            cursor = organizations['pageInfo']['endCursor']
            has_next_page = organizations['pageInfo']['hasNextPage']            
            for org in all_organizations:
                logging.info(f"Processing organization: {org['login']}")
                user_result = fetch_copilot_seats(org['login'],page)
                if user_result is None:
                    continue
                print(user_result)
                for seat in user_result:
                    logging.info(f"{org['name']} {seat['assignee']['login']} {seat['last_activity_at']} {seat['last_activity_editor']}")
                    if seat['last_activity_at'] is None:
                        status = 'Inactive'
                    else:
                        last_activity_date = datetime.strptime(seat['last_activity_at'], '%Y-%m-%dT%H:%M:%S%z')
                        difference = current_date - last_activity_date

                        status = 'Inactive' if difference.days > active_days else 'Active'

                    f.write(f"{org['name']},{seat['assignee']['login']},{seat['last_activity_at']},{seat['last_activity_editor']},{status}\n")

if __name__ == "__main__":
    main()
