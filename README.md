# SlackWave

SlackWave is a Slack automation application that includes SMS sending and user invitation functionality.

## Installation

First, install the required libraries:

```bash
pip install -r requirements.txt
```
## Usage
```bash
python3 app.py
```
## After Running

- **The main page will open.**
[Login](https://github.com/user-attachments/assets/60de4fda-d0af-41c6-a8e6-6036a28e33c8)
- **Click "Creat an account."**
[Sign up](https://github.com/user-attachments/assets/16d7c5ea-bb79-4788-8445-ccea00ddd1a3)
- **You will need a Slack user token to register and use this tool.**
## How to Obtain a Slack Token 
- Go to [Slack Sign In ](https://slack.com/signin#/signin) aand log in or create your Slack workspace.
- After logging in, visit [Slack API Apps](https://api.slack.com/apps) to create a new app. You will see a screen like this: [Create](https://github.com/user-attachments/assets/68263d71-9577-477b-bda0-cdc168a0b13d)
- Choose From scratch: [Scratch](https://github.com/user-attachments/assets/1dd6b0af-5bfe-42f1-ae20-cff83784f18b)
- Set a name and select your workspace: [App Create](https://github.com/user-attachments/assets/cdf17532-9bfb-4c1a-980d-34a60e3091a0)
- Go to the OAuth & Permissions section: [OAuth & Permissions](https://github.com/user-attachments/assets/c9fd0648-76ed-4926-9fc1-b34e9720364b)
- Scroll to the Scopes section, where you'll find User Token Scopes: [Scopes](https://github.com/user-attachments/assets/e6e84db6-89a9-428a-8248-47abbdf145e6)
- Add the following permissions:
```
channels:history - View messages and other content in a user’s public channels

channels:read - View basic information about public channels in a workspace

channels:write - Manage a user’s public channels and create new ones on a user’s behalf

channels:write.invites - Invite members to public channels

chat:write - Send messages on a user’s behalf

files:write - Upload, edit, and delete files on a user’s behalf

groups:read - View basic information about a user’s private channels

groups:write - Manage a user’s private channels and create new ones on a user’s behalf

users:read - View people in a workspace

users:read.email - View email addresses of people in a workspace
```

## Authors

- [@mahammadsultanov](https://www.github.com/mahammadsultanov)
