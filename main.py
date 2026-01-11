"""
main.py - Streamlit frontend + chat interface for NomNom Restaurant Assistant
"""

import streamlit as st
from session_state import (
    init_session_state,
    get_messages,
    add_message,
    get_user_data,
    clear_session,
    is_guest_initialized,
    get_chat_history,
    set_chat_history,
    is_authenticated,
)
from agent import agent

# Page config
st.set_page_config(
    page_title="NomNom - Restaurant Assistant", page_icon="🍽️", layout="centered"
)

# Initialize session state
init_session_state()


def render_sidebar():
    """Render the sidebar with user status and controls."""
    with st.sidebar:
        st.title("🍽️ NomNom")
        st.markdown("---")

        # User status section
        st.subheader("Session Status")
        user_data = get_user_data()

        if user_data.get("is_authenticated"):
            st.success(f"✅ Logged in: {user_data.get('phone')}")
        elif user_data.get("guest_id"):
            st.info(f"👤 Guest: {user_data.get('guest_id')[:8]}...")
        else:
            st.warning("⏳ Initializing...")

        st.markdown("---")

        # Login section (only show if not authenticated)
        if not user_data.get("is_authenticated"):
            st.subheader("Login")
            st.caption("Login to access your account")

            with st.form("login_form"):
                phone = st.text_input(
                    "Phone number", placeholder="+1234567890"
                )
                otp = st.text_input(
                    "OTP (if received)", placeholder="123456"
                )

                col1, col2 = st.columns(2)
                with col1:
                    send_otp = st.form_submit_button("Send OTP")
                with col2:
                    verify = st.form_submit_button("Verify")

                if send_otp and phone:
                    # Request OTP through chat
                    add_message("user", f"I want to login with phone number {phone}")
                    st.rerun()

                if verify and phone and otp:
                    # Verify OTP through chat
                    add_message("user", f"My OTP is {otp} for phone {phone}")
                    st.rerun()
        else:
            # Show orders for logged-in users
            st.subheader("My Orders")
            orders = user_data.get("orders", [])
            if orders:
                for order in orders:
                    with st.expander(f"🧾 Order {order.get('id', 'N/A')[:8]}..."):
                        st.write(f"**Status:** {order.get('status', 'N/A')}")
                        if order.get("total"):
                            st.write(f"**Total:** ${order.get('total', 0):.2f}")
            else:
                st.caption("No orders yet")

        st.markdown("---")

        # Quick actions
        st.subheader("Quick Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Browse", use_container_width=True):
                add_message("user", "Show me some restaurants")
                st.rerun()

        with col2:
            if st.button("🛒 Cart", use_container_width=True):
                add_message("user", "Show my cart")
                st.rerun()

        st.markdown("---")

        # Dev controls
        if st.button("🗑️ Clear Session", use_container_width=True):
            clear_session()
            st.rerun()

        st.caption("Made with ❤️ using Groq")


def render_chat():
    """Render the main chat interface."""
    st.title("🍽️ Restaurant Assistant")

    # Display chat messages
    messages = get_messages()
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Initialize guest session on first load
    if not is_guest_initialized() and len(messages) == 0:
        with st.chat_message("assistant"):
            with st.spinner("Setting up your session..."):
                welcome = agent.initialize_guest()
            st.markdown(welcome)
        add_message("assistant", welcome)
        st.rerun()

    # Process any pending messages that need agent response
    if messages and messages[-1]["role"] == "user":
        user_msg = messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get chat history for context
                history = get_chat_history()
                response = agent.send_message(user_msg, history if history else None)
                # Update stored history
                set_chat_history(agent.get_history())
            st.markdown(response)
        add_message("assistant", response)
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask me about restaurants..."):
        # Add user message
        add_message("user", prompt)
        st.rerun()


def main():
    """Main application entry point."""
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
