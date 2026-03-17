"""
agent.py - Core agent logic with Groq client + tool calling
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api_client import api_client
from session_state import (
    get_user_data,
    set_guest_session,
    set_authenticated_session,
    add_order,
    get_auth_token,
)
from system_prompt import SYSTEM_PROMPT

load_dotenv()

# Initialize Groq client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

client = Groq(api_key=GROQ_API_KEY)
# MODEL_ID = "llama-3.3-70b-versatile"  # Fast model with function calling support
MODEL_ID = "meta-llama/llama-prompt-guard-2-86m" # less token usage

# === Tool Functions ===
# These functions are called by the agent and interact with the backend API


def guest_login() -> dict:
    """
    Create a guest session to start using the restaurant assistant.
    Call this when the user first starts the conversation.
    Returns guest_id and auth token.
    """
    result = api_client.guest_login()
    if "error" not in result:
        guest_id = result.get("user_id")
        token = result.get("access_token")
        if guest_id and token:
            set_guest_session(guest_id, token)
            return {
                "success": True,
                "guest_id": guest_id,
                "message": "Guest session created successfully",
            }
    return {
        "success": False,
        "error": result.get("error", "Failed to create guest session"),
    }


def login(phone: str, otp: Optional[str] = None) -> dict:
    """
    Login with phone number. Two-step process:
    1. First call with just phone number to request OTP
    2. Second call with phone and OTP to verify and complete login

    Args:
        phone: User's phone number (e.g., "+1234567890")
        otp: One-time password received via SMS (optional, for verification step)
    """
    if otp is None:
        # Step 1: Request OTP
        result = api_client.request_otp(phone)
        if "error" not in result:
            return {
                "success": True,
                "step": "otp_sent",
                "message": f"OTP sent to {phone}. Please provide the OTP to complete login.",
            }
        return {"success": False, "error": result.get("error", "Failed to send OTP")}
    else:
        # Step 2: Verify OTP
        result = api_client.verify_otp(phone, otp)
        if "error" not in result:
            token = result.get("access_token") or result.get("token")
            if token:
                set_authenticated_session(phone, token)
                return {
                    "success": True,
                    "step": "authenticated",
                    "message": f"Successfully logged in as {phone}",
                }
        return {"success": False, "error": result.get("error", "Invalid OTP")}


def get_restaurants() -> dict:
    """
    Lists all restaurants. Returns in nearest order if address is updated in user profile.
    """
    # Ensure API client has current token
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.get_restaurants()
    if "error" in result:
        return {"success": False, "error": result["error"]}

    # Handle both list and dict responses
    restaurants = (
        result
        if isinstance(result, list)
        else result.get("restaurants", result.get("data", []))
    )

    return {"success": True, "count": len(restaurants), "restaurants": restaurants}


def get_restaurant_details(restaurant_id: str) -> dict:
    """
    Get detailed information about a specific restaurant including menu, hours, and reviews.

    Args:
        restaurant_id: The unique identifier of the restaurant
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.get_restaurant_details(restaurant_id)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "restaurant": result}


def get_restaurant_menu(restaurant_id: str) -> dict:
    """
    Get the menu for a specific restaurant.

    Args:
        restaurant_id: The unique identifier of the restaurant
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.get_restaurant_menu(restaurant_id)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "menu": result}


def get_cart() -> dict:
    """
    Get the current user's shopping cart with all items.
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.get_cart()
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "cart": result}


def add_to_cart(menu_item_id: str, quantity: int = 1) -> dict:
    """
    Add a menu item to the cart.

    Args:
        menu_item_id: The unique identifier of the menu item to add
        quantity: Number of items to add (default: 1)
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.add_to_cart(menu_item_id, quantity)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {
        "success": True,
        "cart": result,
        "message": f"Added {quantity} item(s) to cart",
    }


def remove_from_cart(menu_item_id: str) -> dict:
    """
    Remove an item completely from the cart.

    Args:
        menu_item_id: The unique identifier of the menu item to remove
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.remove_from_cart(menu_item_id)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "cart": result, "message": "Item removed from cart"}


def update_cart_quantity(menu_item_id: str, quantity: int) -> dict:
    """
    Decrease the quantity of an item in the cart.

    Args:
        menu_item_id: The unique identifier of the menu item
        quantity: Amount to decrease by
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.decrement_cart_item(menu_item_id, quantity)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "cart": result}


def clear_cart() -> dict:
    """
    Remove all items from the cart.
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.clear_cart()
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "message": "Cart cleared"}


def checkout(note: Optional[str] = None) -> dict:
    """
    Checkout the current cart and create an order.

    Args:
        note: Optional special instructions or notes for the order
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.checkout(note)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    # Store order locally
    if "id" in result:
        add_order(result)

    return {"success": True, "order": result, "message": "Order placed successfully!"}


def get_orders() -> dict:
    """
    Get the user's order history.
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.get_orders()
    if "error" in result:
        return {"success": False, "error": result["error"]}

    orders = result if isinstance(result, list) else result.get("orders", [])
    return {"success": True, "orders": orders}


def get_order_details(order_id: str) -> dict:
    """
    Get detailed information about a specific order including invoice.

    Args:
        order_id: The unique identifier of the order
    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.get_order(order_id)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {"success": True, "order": result}


def get_current_user_info() -> dict:
    """
    Get the current user's profile information along with address.
    Works for both guest and authenticated users.
    """
    user_data = get_user_data()

    # Return local data for guest or if API fails
    local_info = {
        "guest_id": user_data.get("guest_id"),
        "phone": user_data.get("phone"),
        "is_authenticated": user_data.get("is_authenticated"),
        "orders": user_data.get("orders", []),
        "address": user_data.get("address", {}),
    }

    if not user_data.get("is_authenticated"):
        return {
            "success": True,
            "user_type": "guest",
            "info": local_info,
            "message": "You're browsing as a guest. Login with your phone to access full features.",
        }

    # Try to get more info from API
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.get_current_user()
    if "error" not in result:
        local_info.update(result)

    return {"success": True, "user_type": "authenticated", "info": local_info}


def search(
    query: str, filters: dict = None, page: int = 1, limit: int = None, type: str = None
) -> dict:
    """
    Search for anything about restaurants, food, or dining.
    Unified search endpoint.
    """
    result = api_client.search(
        query=query, filters=filters, page=page, limit=limit, type=type
    )

    if "error" in result:
        return {"success": False, "error": result["error"]}
    return {"success": True, "results": result}


def update_address(address: dict) -> dict:
    """
    Update the user's address in their profile.

        params: {
            latitude: float,
            longitude: float,

            line1: str | None,
            line2: str | None,
            landmark: str | None,
            city: str | None,
            state: str | None,
            postal_code: str | None,
            country: str | None,
        }

    """
    token = get_auth_token()
    if token:
        api_client.set_token(token)

    result = api_client.update_address(address)
    if "error" in result:
        return {"success": False, "error": result["error"]}

    return {
        "success": True,
        "message": "Address updated successfully",
        "address": result,
    }


# === Tool Definitions for Groq (OpenAI-compatible format) ===

TOOL_FUNCTIONS = {
    "guest_login": guest_login,
    "login": login,
    "get_restaurants": get_restaurants,
    "get_restaurant_details": get_restaurant_details,
    "get_restaurant_menu": get_restaurant_menu,
    "get_cart": get_cart,
    "add_to_cart": add_to_cart,
    "remove_from_cart": remove_from_cart,
    "update_cart_quantity": update_cart_quantity,
    "clear_cart": clear_cart,
    "checkout": checkout,
    "get_orders": get_orders,
    "get_order_details": get_order_details,
    "get_current_user_info": get_current_user_info,
    "search": search,
    "update_address": update_address,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "guest_login",
            "description": "Create a guest session to start using the restaurant assistant.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "login",
            "description": "Login with phone number. First call with just phone to request OTP, then call with phone and OTP to verify.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "User's phone number (e.g., +1234567890)",
                    },
                    "otp": {
                        "type": "string",
                        "description": "One-time password received via SMS (optional, for verification step)",
                    },
                },
                "required": ["phone"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurants",
            "description": "Lists all restaurants. Returns in nearest order if address is updated in user profile.",
            "parameters": {},
        },
        "required": [],
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_details",
            "description": "Get detailed information about a specific restaurant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "string",
                        "description": "The unique identifier of the restaurant",
                    },
                },
                "required": ["restaurant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_restaurant_menu",
            "description": "Get the menu for a specific restaurant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_id": {
                        "type": "string",
                        "description": "The unique identifier of the restaurant",
                    },
                },
                "required": ["restaurant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cart",
            "description": "Get the current user's shopping cart with all items.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a menu item to the cart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "menu_item_id": {
                        "type": "string",
                        "description": "The unique identifier of the menu item",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of items to add (default: 1)",
                    },
                },
                "required": ["menu_item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove an item completely from the cart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "menu_item_id": {
                        "type": "string",
                        "description": "The unique identifier of the menu item to remove",
                    },
                },
                "required": ["menu_item_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_cart_quantity",
            "description": "Decrease the quantity of an item in the cart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "menu_item_id": {
                        "type": "string",
                        "description": "The unique identifier of the menu item",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Amount to decrease by",
                    },
                },
                "required": ["menu_item_id", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_cart",
            "description": "Remove all items from the cart.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkout",
            "description": "Checkout the current cart and create an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {
                        "type": "string",
                        "description": "Optional special instructions for the order",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_orders",
            "description": "Get the user's order history.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get detailed information about a specific order including invoice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The unique identifier of the order",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_user_info",
            "description": "Get the current user's profile information including past orders.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search for anything related to restaurants, food, or dining.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string",
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filters to refine the search eg. {max_price, min_price, is_available, restaurant_id, city}. This should be a key, value map data type, do not pass these params as arguements in the function directly.",
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination (default: 1)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results per page (optional)",
                    },
                    "type": {
                        "type": "string",
                        "description": "Type of search (e.g., restaurant, menu item)",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_address",
            "description": "Update the user's address in their profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "object",
                        "description": "Address details including latitude, longitude, line1, line2, landmark, city, state, postal_code, country",
                    },
                },
                "required": ["address"],
            },
        },
    },
]


class RestaurantAgent:
    """Groq-powered restaurant assistant agent."""

    def __init__(self):
        logger.info(msg="[RestaurantAgent Constructor] Restaurant Agent is Online!")
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _execute_tool_call(self, tool_call) -> str:
        """Execute a tool call and return the result as JSON string."""
        logger.info("[RestaurantAgent] _execute_tool_call invoked")
        function_name = tool_call.function.name
        try:
            logger.info(f"[RestaurantAgent] _execute_tool_call function_name: {function_name}")
            arguments = json.loads(tool_call.function.arguments) or {}
        except json.JSONDecodeError:
            logger.info(f"[RestaurantAgent] _execute_tool_call JSONDecodeError for arguments")
            arguments = {}
        
        if function_name in TOOL_FUNCTIONS:
            logger.info(f"[RestaurantAgent] _execute_tool_call  executing function: {function_name} with arguments: {arguments}")
            result = TOOL_FUNCTIONS[function_name](**arguments)
            logger.info(f"[RestaurantAgent] _execute_tool_call result: {result}")
        else:
            logger.info(f"[RestaurantAgent] _execute_tool_call error unknown function: {function_name}")
            result = {"error": f"Unknown function: {function_name}"}

        return json.dumps(result)

    def send_message(self, message: str, history: list = None) -> str:
        """
        Send a message and get a response.
        Handles tool calling with Groq's OpenAI-compatible API.
        """
        try:
            # Use provided history or current messages
            if history is not None:
                self.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

            # Add user message
            self.messages.append({"role": "user", "content": message})
            logger.info(f"[RestaurantAgent] send_message invoked with message: {message}")
            # Send to Groq
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=4096,
            )
            logger.info(f"[RestaurantAgent] send_message received response: {response}")

            response_message = response.choices[0].message
            logger.info(f"[RestaurantAgent] send_message response_message: {response_message}")

            # Check if model wants to call tools
            while response_message.tool_calls:
                # Add assistant message with tool calls
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in response_message.tool_calls
                        ],
                    }
                )
                logger.info(f"[RestaurantAgent] send_message tool_calls detected: {response_message.tool_calls}")

                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    logger.info(f"[RestaurantAgent] send_message executing tool_call: {tool_call}")
                    result = self._execute_tool_call(tool_call)
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
                    logger.info(f"[RestaurantAgent] send_message tool_call result added to messages")
                # Get next response
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=self.messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=4096,
                )
                logger.info(f"[RestaurantAgent] send_message received next response: {response}")
                response_message = response.choices[0].message

            # Add final assistant response to history
            assistant_content = response_message.content or ""
            logger.info(f"[RestaurantAgent] send_message final assistant response: {assistant_content}")
            self.messages.append({"role": "assistant", "content": assistant_content})
            
            return assistant_content

        except Exception as e:
            logger.error(f"[RestaurantAgent] send_message encountered error: {e}")
            error_msg = str(e)
            if "rate" in error_msg.lower() or "quota" in error_msg.lower():
                return "I'm currently experiencing high demand. Please try again in a moment."
            elif "invalid" in error_msg.lower() and "api" in error_msg.lower():
                return (
                    "There's an issue with my configuration. Please check the API key."
                )
            else:
                return f"I encountered an issue: {error_msg}. Let me try to help you another way."

    def get_history(self) -> list:
        """Get the current chat history (excluding system message)."""
        return [msg for msg in self.messages if msg["role"] != "system"]

    def clear_history(self):
        """Clear chat history, keeping only system message."""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def initialize_guest(self) -> str:
        """Initialize guest session and return welcome message."""
        result = guest_login()

        if result.get("success"):
            return (
                "Welcome to NomNom! 🍽️ I'm your restaurant assistant.\n\n"
                "I've set up a guest session for you. Here's what you can do:\n"
                "• **Browse restaurants** by city or cuisine\n"
                "• **View menus** and add items to your cart\n"
                "• **Place orders** for pickup or delivery\n\n"
                "How can I help you today? Would you like to explore some restaurants?"
            )
        else:
            return (
                "Welcome to NomNom! 🍽️ I'm your restaurant assistant.\n\n"
                "I had a small hiccup setting up, but I'm still here to help!\n"
                "What would you like to do? I can help you find great food."
            )


# Singleton agent instance
agent = RestaurantAgent()
