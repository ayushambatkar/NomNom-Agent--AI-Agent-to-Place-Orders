"""
api_client.py - Simple HTTP client for backend API calls
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000")


class APIClient:
    """HTTP client for restaurant backend API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None

    def set_token(self, token: str):
        """Set the auth token for authenticated requests."""
        self.token = token

    def _headers(self, authenticated: bool = False) -> dict:
        """Build request headers."""
        headers = {"Content-Type": "application/json"}
        if authenticated and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(self, response: requests.Response) -> dict:
        """Handle API response, return JSON or error dict."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                return {
                    "error": error_data.get("message", str(e)),
                    "status": response.status_code,
                }
            except:
                return {"error": str(e), "status": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
        except ValueError:
            return {"error": "Invalid JSON response"}

    # === Auth Endpoints ===

    def guest_login(self) -> dict:
        """Create a guest session. POST /api/v1/auth/guest"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth/guest", headers=self._headers()
            )
            result = self._handle_response(response)
            if "access_token" in result:
                self.token = result["access_token"]
            return result
        except Exception as e:
            return {"error": f"Guest login failed: {str(e)}"}

    def request_otp(self, phone: str) -> dict:
        """Request OTP for phone login. POST /api/v1/auth/request-otp"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/request-otp",
                headers=self._headers(),
                json={"phone": phone},
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"OTP request failed: {str(e)}"}

    def verify_otp(self, phone: str, otp: str) -> dict:
        """Verify OTP and complete login. POST /api/v1/auth/verify-otp"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/verify-otp",
                headers=self._headers(),
                json={"phone": phone, "otp": otp},
            )
            result = self._handle_response(response)
            if "access_token" in result:
                self.token = result["access_token"]
            return result
        except Exception as e:
            return {"error": f"OTP verification failed: {str(e)}"}

    # === Restaurant Endpoints ===

    def get_restaurants(
        self,    ) -> dict:
        """Get list of restaurants. GET /api/v1/restaurants"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/restaurants",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch restaurants: {str(e)}"}

    def get_restaurant_details(self, restaurant_id: str) -> dict:
        """Get restaurant details. GET /api/v1/restaurants/{id}"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/restaurants/{restaurant_id}",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch restaurant: {str(e)}"}

    def get_restaurant_menu(self, restaurant_id: str) -> dict:
        """Get restaurant menu. GET /api/v1/restaurants/menu-items/{id}"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/restaurants/menu-items/{restaurant_id}",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch menu: {str(e)}"}

    # === Cart Endpoints ===

    def get_cart(self) -> dict:
        """Get current user's cart. GET /api/v1/cart"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/cart",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch cart: {str(e)}"}

    def add_to_cart(self, menu_item_id: str, quantity: int = 1) -> dict:
        """Add item to cart. POST /api/v1/cart/add"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/cart/add",
                headers=self._headers(authenticated=True),
                json={"menu_item_id": menu_item_id, "quantity": quantity},
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to add to cart: {str(e)}"}

    def remove_from_cart(self, menu_item_id: str) -> dict:
        """Remove item from cart. DELETE /api/v1/cart/item/{menuItemId}"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/cart/item/{menu_item_id}",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to remove from cart: {str(e)}"}

    def decrement_cart_item(self, menu_item_id: str, quantity: int = 1) -> dict:
        """Decrement item quantity in cart. GET /api/v1/cart/decrement"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/cart/decrement",
                headers=self._headers(authenticated=True),
                params={"menuItemId": menu_item_id, "quantity": quantity},
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to decrement cart item: {str(e)}"}

    def clear_cart(self) -> dict:
        """Clear all items from cart. POST /api/v1/cart/clear"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/cart/clear",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to clear cart: {str(e)}"}

    # === Order Endpoints ===

    def checkout(self, note: Optional[str] = None) -> dict:
        """Checkout current cart and create order. POST /api/v1/orders/checkout"""
        try:
            body = {}
            if note:
                body["note"] = note
            response = requests.post(
                f"{self.base_url}/api/v1/orders/checkout",
                headers=self._headers(authenticated=True),
                json=body,
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to checkout: {str(e)}"}

    def get_orders(self) -> dict:
        """Get user's order history. GET /api/v1/orders"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/orders",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch orders: {str(e)}"}

    def get_order(self, order_id: str) -> dict:
        """Get order details/invoice. GET /api/v1/orders/{id}"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/orders/{order_id}",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch order: {str(e)}"}

    # === User Endpoints ===

    def get_current_user(self) -> dict:
        """Get current user profile. GET /api/v1/users/me"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/users/me",
                headers=self._headers(authenticated=True),
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to fetch user: {str(e)}"}

    def search(
        self,
        query: str,
        filters: dict = None,
        page: int = 1,
        limit: int = None,
        type: str = None,
    ) -> dict:
        """Search restaurants and menu items. GET /api/v1/search"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/search",
                headers=self._headers(authenticated=True),
                params={
                    "query": query,
                    "filters": filters,
                    "page": page,
                    "limit": limit,
                    "type": type,
                },
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def update_address(self, address: dict) -> dict:
        """Update user address. PUT /api/v1/users/address
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
        try:
            response = requests.put(
                f"{self.base_url}/api/v1/users/address",
                headers=self._headers(authenticated=True),
                json=address,
            )
            return self._handle_response(response)
        except Exception as e:
            return {"error": f"Failed to update address: {str(e)}"}


# Singleton instance
api_client = APIClient()
