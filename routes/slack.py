from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from utils.slack_utils import get_slack_client, get_channels, upload_file_to_slack
from slack_sdk.errors import SlackApiError
import os
import tempfile
from utils.import_mails import process_excel_file
import re

slack_bp = Blueprint('slack', __name__)

@slack_bp.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the username from session
    username = session.get('username', '')
    return render_template('index.html', username=username)

@slack_bp.route("/sms-sender", methods=["GET", "POST"])
def sms_sender():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the username from session
    username = session.get('username', '')
    client = get_slack_client(session)
    
    if not client:
        return redirect(url_for('auth.login'))
    
    if request.method == "GET":
        try:
            # Get private and public channels
            private_response = client.conversations_list(types="private_channel")
            public_response = client.conversations_list(types="public_channel")
    
            # Extract the channels from the response
            private_channels = private_response.get("channels", [])
            public_channels = public_response.get("channels", [])
            
            # Create a set of private channel IDs for quick lookup
            private_channel_ids = {channel['id'] for channel in private_channels}
            
            # Combine channels and mark if they're private
            all_channels = []
            for channel in private_channels + public_channels:
                channel['is_private'] = channel['id'] in private_channel_ids
                all_channels.append(channel)
                
            return render_template("sms-sender.html", channels=all_channels, username=username)
        except SlackApiError as e:
            all_channels = []
            return render_template("sms-sender.html", channels=all_channels, username=username)

    # Handle the POST request
    selected_channels = request.form.getlist("channels")
    message = request.form.get("message")
    image = request.files.get("photo")

    if not selected_channels:
        return jsonify({"success": False, "message": "Please select at least one channel"})

    if not client:
        return jsonify({"success": False, "message": "Not authenticated"})

    message_errors = []
    if message:
        for channel_id in selected_channels:
            try:
                client.chat_postMessage(channel=channel_id, text=message)
            except SlackApiError as e:
                message_errors.append(f"Error sending to {channel_id}: {str(e)}")

    file_error = None
    if image and image.filename:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as temp_file:
            image.save(temp_file.name)
            success, msg = upload_file_to_slack(client, temp_file.name, selected_channels)
            if not success:
                file_error = msg
        os.unlink(temp_file.name)

    if message_errors or file_error:
        error_message = ". ".join(message_errors)
        if file_error:
            error_message += f" File upload error: {file_error}"
        return jsonify({"success": False, "message": error_message})
    
    return jsonify({"success": True, "message": "Message and files sent successfully"})

@slack_bp.route("/user-invite", methods=["GET"])
def user_invite():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the username from session
    username = session.get('username', '')
    client = get_slack_client(session)
    
    if not client:
        return redirect(url_for('auth.login'))
    
    try:
        # Get private and public channels
        private_response = client.conversations_list(types="private_channel")
        public_response = client.conversations_list(types="public_channel")

        # Extract the channels from the response
        private_channels = private_response.get("channels", [])
        public_channels = public_response.get("channels", [])
        
        # Create a set of private channel IDs for quick lookup
        private_channel_ids = {channel['id'] for channel in private_channels}
        
        # Combine channels and mark if they're private
        all_channels = []
        for channel in private_channels + public_channels:
            channel['is_private'] = channel['id'] in private_channel_ids
            all_channels.append(channel)
            
        return render_template("user-invite.html", channels=all_channels, username=username)
    except SlackApiError as e:
        all_channels = []
        return render_template("user-invite.html", channels=all_channels, username=username)

@slack_bp.route("/add-to-channel", methods=["POST"])
def add_to_channel():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not authenticated"})
    
    client = get_slack_client(session)
    
    if not client:
        return jsonify({"success": False, "message": "Not authenticated"})
    
    # Get form data
    email_input = request.form.get("email", "")
    selected_channels = request.form.getlist("channels")
    
    if not email_input:
        return jsonify({"success": False, "message": "Please provide at least one email address"})
    
    if not selected_channels:
        return jsonify({"success": False, "message": "Please select at least one channel"})
    
    # Split the email input by common separators (newline, comma, semicolon)
    emails = [e.strip() for e in re.split(r'[\n,;]+', email_input) if e.strip()]
    
    if not emails:
        return jsonify({"success": False, "message": "Please provide valid email addresses"})
    
    # Process each email
    success_count = 0
    failed_emails = []
    
    for email in emails:
        # Try to get the user ID from the email
        try:
            user_info = client.users_lookupByEmail(email=email)
            user_id = user_info["user"]["id"]
            
            # Add user to each selected channel
            channel_errors = []
            channel_success = 0
            
            for channel_id in selected_channels:
                try:
                    # Try to invite the user to the channel
                    result = client.conversations_invite(
                        channel=channel_id,
                        users=[user_id]
                    )
                    channel_success += 1
                except SlackApiError as e:
                    if "already_in_channel" in str(e):
                        # Count this as a success if user is already in channel
                        channel_success += 1
                    else:
                        channel_errors.append(f"{channel_id}: {str(e)}")
            
            if channel_success == len(selected_channels):
                success_count += 1
            else:
                failed_emails.append(f"{email} (added to {channel_success}/{len(selected_channels)} channels)")
                
        except SlackApiError as e:
            failed_emails.append(f"{email}: {str(e)}")
    
    # Prepare response message
    if success_count == len(emails):
        return jsonify({
            "success": True, 
            "message": f"Successfully added {success_count} users to {len(selected_channels)} channels"
        })
    elif success_count > 0:
        return jsonify({
            "success": True, 
            "message": f"Added {success_count}/{len(emails)} users. Failed: {', '.join(failed_emails)}"
        })
    else:
        return jsonify({
            "success": False, 
            "message": f"Failed to add any users. Errors: {', '.join(failed_emails)}"
        })

@slack_bp.route("/read-excel", methods=['POST'])
def read_excel():
    if 'username' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    client = get_slack_client(session)
    
    if not client:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "message": "No file part in the request"
        }), 400
        
    file = request.files['file']
    result, status_code = process_excel_file(file)
    
    return jsonify(result), status_code