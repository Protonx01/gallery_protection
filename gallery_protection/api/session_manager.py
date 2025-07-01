import frappe
import uuid
import time
import json
from frappe import _
from frappe.utils import now_datetime, add_to_date
import hashlib

@frappe.whitelist(allow_guest=True)
def create_viewing_session():
    """
    Create a temporary viewing session for unauthenticated users
    Returns session token with expiry time
    """
    if frappe.local.request.method != "POST":
        frappe.throw(_("Invalid request method. Use POST."), frappe.PermissionError)

    try:
        # Get client IP for additional security
        client_ip = frappe.local.request_ip or "unknown"
        user_agent = frappe.get_request_header("User-Agent") or "unknown"
        
        # Check rate limiting - max 5 sessions per IP per hour
        if not check_session_rate_limit(client_ip):
            return {
                "success": False,
                "message": "Too many session requests from this IP. Please try again later.",
                "retry_after": 3600
            }
        
        # Generate unique session token
        session_token = str(uuid.uuid4())
        
        # Session expires in 2 hours
        expires_at = add_to_date(now_datetime(), hours=2)
        
        # Create session data
        session_data = {
            "token": session_token,
            "created_at": now_datetime().isoformat(),
            "expires_at": expires_at.isoformat(),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "image_requests": 0,  # Counter for rate limiting
            "max_requests": 200,  # Max 200 image requests per session
            "is_active": True
        }
        
        # Store session in cache (Redis if available, else database)
        cache_key = f"viewing_session:{session_token}"
        frappe.cache().set_value(cache_key, json.dumps(session_data), expires_in_sec=7200)  # 2 hours
        
        # Log session creation
        frappe.logger().info(f"Viewing session created: {session_token} for IP: {client_ip}")
        
        return {
            "success": True,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": 7200,
            "max_image_requests": 200,
            "message": "Viewing session created successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating viewing session: {str(e)}")
        return {
            "success": False,
            "message": "Error creating viewing session",
            "error": str(e)
        }

def increment_session_usage(session_token):
    """
    Increment the image request counter for a session
    """
    try:
        cache_key = f"viewing_session:{session_token}"
        session_data_str = frappe.cache().get_value(cache_key)
        
        if session_data_str:
            session_data = json.loads(session_data_str)
            session_data["image_requests"] = session_data.get("image_requests", 0) + 1
            
            # Update cache with new counter
            frappe.cache().set_value(cache_key, json.dumps(session_data), expires_in_sec=7200)
            
            return session_data["image_requests"]
    except Exception as e:
        frappe.log_error(f"Error incrementing session usage: {str(e)}")
    
    return 0

def check_session_rate_limit(client_ip):
    """
    Check if IP has exceeded session creation rate limit
    """
    try:
        # Rate limit key
        rate_limit_key = f"session_rate_limit:{client_ip}"
        
        # Get current count
        current_count = frappe.cache().get_value(rate_limit_key) or 0
        
        if int(current_count) >= 5:  # Max 5 sessions per IP per hour
            return False
        
        # Increment counter
        frappe.cache().set_value(rate_limit_key, int(current_count) + 1, expires_in_sec=3600)  # 1 hour
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error checking rate limit: {str(e)}")
        return True  # Allow if there's an error

@frappe.whitelist()
def get_session_stats(session_token):
    """
    Get statistics for a viewing session (for admin/debugging)
    Requires authentication
    """
    try:
        cache_key = f"viewing_session:{session_token}"
        session_data_str = frappe.cache().get_value(cache_key)
        
        if not session_data_str:
            return {
                "success": False,
                "message": "Session not found"
            }
        
        session_data = json.loads(session_data_str)
        
        return {
            "success": True,
            "session_stats": {
                "token": session_data["token"],
                "created_at": session_data["created_at"],
                "expires_at": session_data["expires_at"],
                "client_ip": session_data["client_ip"],
                "image_requests": session_data.get("image_requests", 0),
                "max_requests": session_data.get("max_requests", 200),
                "is_active": session_data.get("is_active", True)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting session stats: {str(e)}")
        return {
            "success": False,
            "message": "Error retrieving session stats"
        }

@frappe.whitelist()
def revoke_viewing_session(session_token):
    """
    Revoke/deactivate a viewing session (admin only)
    Requires authentication
    """
    try:
        cache_key = f"viewing_session:{session_token}"
        session_data_str = frappe.cache().get_value(cache_key)
        
        if not session_data_str:
            return {
                "success": False,
                "message": "Session not found"
            }
        
        session_data = json.loads(session_data_str)
        session_data["is_active"] = False
        
        # Update cache
        frappe.cache().set_value(cache_key, json.dumps(session_data), expires_in_sec=7200)
        
        frappe.logger().info(f"Viewing session revoked: {session_token}")
        
        return {
            "success": True,
            "message": "Session revoked successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"Error revoking session: {str(e)}")
        return {
            "success": False,
            "message": "Error revoking session"
        }

@frappe.whitelist(allow_guest=True)
def refresh_viewing_session():
    if frappe.local.request.method != "POST":
        frappe.throw(_("Invalid request method. Use POST."), frappe.PermissionError)

    session_token = frappe.form_dict.get("session_token")
    if not session_token:
        return {
            "success": False,
            "message": "No session token provided"
        }

    validation_result = validate_viewing_session_internal(session_token)  
    if not validation_result["valid"]:
        return validation_result       
    # Extend session by 2 more hours
    cache_key = f"viewing_session:{session_token}"
    session_data = validation_result["session_data"]
        
    # Update expiry time
    new_expires_at = add_to_date(now_datetime(), hours=2)
    session_data["expires_at"] = new_expires_at.isoformat()
        
    # Update cache
    frappe.cache().set_value(cache_key, json.dumps(session_data), expires_in_sec=7200)
        
    return {
        "success": True,
        "message": "Session refreshed successfully",
        "expires_at": new_expires_at.isoformat(),
        "expires_in_seconds": 7200
    }
        
def validate_viewing_session_internal(session_token):
    try:
        cache_key = f"viewing_session:{session_token}"
        session_data_str = frappe.cache().get_value(cache_key)

        if not session_data_str:
            return {
                "valid": False,
                "message": "Session not found or expired"
            }

        session_data = json.loads(session_data_str)

        if not session_data.get("is_active", False):
            return {
                "valid": False,
                "message": "Session has been deactivated"
            }

        expires_at = frappe.utils.get_datetime(session_data["expires_at"])
        if now_datetime() > expires_at:
            frappe.cache().delete_value(cache_key)
            return {
                "valid": False,
                "message": "Session has expired"
            }

        if session_data.get("image_requests", 0) >= session_data.get("max_requests", 200):
            return {
                "valid": False,
                "message": "Session request limit exceeded"
            }

        return {
            "valid": True,
            "session_data": session_data,
            "message": "Session is valid"
        }

    except Exception as e:
        frappe.log_error(f"Error validating session: {str(e)}")
        return {
            "valid": False,
            "message": "Error validating session"
        }

@frappe.whitelist(allow_guest=True)
def validate_viewing_session(session_token):
    # if frappe.local.request.method != "POST":
    #     frappe.throw(_("Invalid request method. Use POST."), frappe.PermissionError)

    if not session_token:
        return {
            "valid": False,
            "message": "No session token provided"
        }

    return validate_viewing_session_internal(session_token)
