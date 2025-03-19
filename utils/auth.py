from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

def get_user_data(username):
    try:
        df = pd.read_csv('users.csv')
        user = df[df['username'] == username].to_dict('records')
        if user:
            return user[0]
        return None
    except Exception as e:
        print(f"Error reading user data: {e}")
        return None

def save_user_data(username, password_hash, slack_token):
    try:
        new_user = {
            'username': username,
            'password': password_hash,
            'slack_token': slack_token
        }
        try:
            df = pd.read_csv('users.csv')
        except FileNotFoundError:
            df = pd.DataFrame(columns=['username', 'password', 'slack_token'])
        
        df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
        df.to_csv('users.csv', index=False)
        return True
    except Exception as e:
        print(f"Error saving user data: {e}")
        return False