"""
session_state.py - Helper to manage persistent session data in Streamlit
"""

import streamlit as st
from typing import Any, Optional


def init_session_state():
    """Initialize all session state variables on first load."""

    # User data - authentication and profile
    if "user_data" not in st.session_state:
        st.session_state["user_data"] = {
            "guest_id": None,
            "auth_token": None,
            "phone": None,
            "is_authenticated": False,
            "orders": [],
            "address": {},
        }

    # Chat history for the conversation
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Chat history for Groq (includes function calls/responses)
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Flag to track if guest login has been done
    if "guest_initialized" not in st.session_state:
        st.session_state["guest_initialized"] = False

    # Login flow state
    if "login_step" not in st.session_state:
        st.session_state["login_step"] = None  # None, "phone_sent", "awaiting_otp"

    if "pending_phone" not in st.session_state:
        st.session_state["pending_phone"] = None


def get_user_data() -> dict:
    """Get the current user data dict."""
    init_session_state()
    return st.session_state["user_data"]


def update_user_data(**kwargs):
    """Update user data with provided key-value pairs."""
    init_session_state()
    for key, value in kwargs.items():
        if key in st.session_state["user_data"]:
            st.session_state["user_data"][key] = value


def set_guest_session(guest_id: str, token: str):
    """Set guest session data after guest login."""
    update_user_data(guest_id=guest_id, auth_token=token, is_authenticated=False)
    st.session_state["guest_initialized"] = True


def set_authenticated_session(phone: str, token: str):
    """Set authenticated user session after phone login."""
    update_user_data(phone=phone, auth_token=token, is_authenticated=True)


def add_order(order: dict):
    """Add an order to the user's list."""
    init_session_state()
    st.session_state["user_data"]["orders"].append(order)


def get_messages() -> list:
    """Get chat messages for display."""
    init_session_state()
    return st.session_state["messages"]


def add_message(role: str, content: str):
    """Add a message to chat history."""
    init_session_state()
    st.session_state["messages"].append({"role": role, "content": content})


def get_chat_history() -> list:
    """Get Gemini chat history."""
    init_session_state()
    return st.session_state["chat_history"]


def set_chat_history(history: list):
    """Set Gemini chat history."""
    init_session_state()
    st.session_state["chat_history"] = history


def clear_session():
    """Clear all session data for a fresh start."""
    keys_to_clear = [
        "user_data",
        "messages",
        "chat_history",
        "guest_initialized",
        "login_step",
        "pending_phone",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    init_session_state()


def is_guest_initialized() -> bool:
    """Check if guest session has been initialized."""
    init_session_state()
    return st.session_state.get("guest_initialized", False)


def get_auth_token() -> Optional[str]:
    """Get the current auth token."""
    return get_user_data().get("auth_token")


def is_authenticated() -> bool:
    """Check if user is fully authenticated (not just guest)."""
    return get_user_data().get("is_authenticated", False)
