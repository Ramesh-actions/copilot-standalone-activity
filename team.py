import requests

## Enter the ENTERPRISE_SLUG, TEAM_NAME_FILTER, and AUTH_TOKEN values below
## Run the script using the command: python get_users.py

# Global constants
ENTERPRISE_SLUG = '' # your_enterprise_slug_here
TEAM_NAME_FILTER = '' # your_team_name_here
AUTH_TOKEN = '' # your_auth_token_here Use token (Classic) with the following scopes: "manage_billing:copilot" or "read:enterprise"

def get_copilot_billing_seats():
    # Construct the API URL using the enterprise slug
    api_url = f"https://api.github.com/enterprises/{ENTERPRISE_SLUG}/copilot/billing/seats"

    # Headers dictionary to include the Authorization header
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }

    # Make the API request with the Authorization header
    response = requests.get(api_url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
    else:
        # Handle errors (e.g., network issues, invalid slug, etc.)
        return f"Error: Received response code {response.status_code}"

    # Filter data based on TEAM_NAME_FILTER and extract "login" from "assignee"
    users_info = [
        {
            'login': item.get('assignee', {}).get('login'), 
            'last_activity_at': item.get('last_activity_at')
        }
        for item in data['seats'] 
        if item.get('assigning_team', {}).get('name') == TEAM_NAME_FILTER 
        and item.get('assignee') 
        and item.get('assignee').get('login')
    ]
    return users_info

# Example usage
if __name__ == "__main__":
    seats_info = get_copilot_billing_seats()
    print(f"Seats Info: {seats_info}")
    print(f"Number of users in '{TEAM_NAME_FILTER}': {len(seats_info)}")
