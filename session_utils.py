# session_utils.py

from flask import session
import secrets

def init_session():
    user_session_id = session.get('user_session_id')
    if user_session_id is None:
        user_session_id = secrets.token_hex(16)
        session['user_session_id'] = user_session_id

def get_user_session_id():
    return session.get('user_session_id')
