from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import pandas as pd
from utils.auth import get_user_data

def get_slack_client(session):
    if 'username' in session:
        user_data = get_user_data(session['username'])
        print(f"Getting Slack client for user: {session['username']}")
        if user_data and user_data['slack_token']:
            return WebClient(token=user_data['slack_token'])
        else:
            print("No Slack token found for user")
    else:
        print("No user in session")
    return None

def get_channels(client=None):
    if not client:
        print("No Slack client available")
        return []
    
    try:
        response = client.conversations_list(types="private_channel,public_channel")
        channels = response["channels"]
        return [{"id": channel["id"], "name": channel["name"]} for channel in channels]
    except SlackApiError as e:
        print(f"Error getting channels: {e}")
        return []

def upload_file_to_slack(client, file_path, channel_ids):
    if not client:
        return False, "Not authenticated"
    
    try:
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as file:
            for channel_id in channel_ids:
                try:
                    response = client.files_upload_v2(
                        channel=channel_id,
                        file=file,
                        filename=os.path.basename(file_path),
                        length=file_size
                    )
                    file.seek(0)
                except SlackApiError as e:
                    print(f"Error uploading file to channel {channel_id}: {e}")
                    return False, str(e)
        return True, "File uploaded successfully"
    except Exception as e:
        print(f"Error in file upload: {e}")
        return False, str(e)