import frappe
import os
from frappe import _
from frappe.utils.file_manager import get_file_path
from werkzeug.wrappers import Response
from werkzeug.utils import secure_filename
import mimetypes
import warnings
from .session_manager import validate_viewing_session_internal, increment_session_usage
from .watermarker import add_watermark, add_watermark_half
import magic

warnings.filterwarnings("ignore", category=DeprecationWarning)

def require_viewing_session(method):
    """
    Decorator to require viewing session for gallery endpoints
    """
    def wrapper(*args, **kwargs):
        try:
            session_token = frappe.get_request_header("X-Session-Token")
            
            if not session_token:
                frappe.throw(_("Missing session token in headers"))
            
            validation_result = validate_viewing_session_internal(session_token)
            if not validation_result.get("valid"):
                return {
                    "success": False,
                    "error": "Session validation failed",
                    "message": validation_result.get("message")
                }

            increment_session_usage(session_token)
            return method(*args, **kwargs)
            
        except Exception as e:
            frappe.log_error(
                title="Session middleware error",
                message=f"{str(e)}\n{frappe.get_traceback()}"
            )
            return {
                "success": False,
                "error": "Session validation failed",
                "message": str(e)
            }
    
    return wrapper

def _get_images(service_id=None, folder_type='gallery'):
    """
    Helper function to get gallery images
    """
    private_path = frappe.get_site_path("private", "files", "images")
    images = []
    supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']

    def process_directory(directory_path, service_name):
        if not os.path.exists(directory_path):
            return

        for filename in os.listdir(directory_path):
            if any(filename.lower().endswith(ext) for ext in supported_formats):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    images.append({
                        "name": filename,
                        "service_id": service_name,
                        "size": file_stat.st_size,
                        "modified": file_stat.st_mtime,
                        "url": f"/api/method/gallery_protection.api.gallery_api.serve_image?service_id={service_name}&folder_type={folder_type}&image_name={filename}"
                    })

    if service_id:
        secure_service_id = secure_filename(service_id)
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        gallery_path = os.path.join(private_path, secure_service_id, folder_type)
        process_directory(gallery_path, service_id)
    else:
        if not os.path.exists(private_path):
            return images
        
        for service_name in os.listdir(private_path):
            service_path = os.path.join(private_path, service_name)
            if not os.path.isdir(service_path):
                continue
            
            gallery_path = os.path.join(service_path, folder_type)
            process_directory(gallery_path, service_name)

    return images

@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_all_gallery_images(cmd=None):
    """
    API endpoint to get list of all gallery images from all services
    """
    try:
        images = _get_images(folder_type='gallery')
        images.sort(key=lambda x: x['modified'], reverse=True)
        return {
            "success": True,
            "message": f"Found {len(images)} images",
            "images": images
        }
    except Exception as e:
        frappe.log_error(f"Error in get_all_gallery_images: {str(e)}")
        return {"success": False, "message": "Error retrieving gallery images", "error": str(e)}

@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_gallery_images_by_id(**kwargs):
    """
    API endpoint to get list of gallery images from a specific service
    """
    service_id = frappe.form_dict.get('service_id')
    if not service_id: frappe.throw(_("Service ID is required"))
    
    try:
        images = _get_images(service_id=service_id, folder_type='gallery')
        images.sort(key=lambda x: x['modified'], reverse=True)
        return {
            "success": True,
            "message": f"Found {len(images)} images for service: {service_id}" if images else f"No photos found for service: {service_id}",
            "images": images
        }
    except Exception as e:
        frappe.log_error(f"Error in get_gallery_images_by_id: {str(e)}")
        return {"success": False, "message": "Error retrieving gallery images", "error": str(e)}

@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_all_half_gallery_images(cmd=None):
    """
    API endpoint to get list of all galleryHalf images from all services
    """
    try:
        images = _get_images(folder_type='galleryHalf')
        images.sort(key=lambda x: x['modified'], reverse=True)
        return {
            "success": True,
            "message": f"Found {len(images)} half gallery images",
            "images": images
        }
    except Exception as e:
        frappe.log_error(f"Error in get_all_half_gallery_images: {str(e)}")
        return {"success": False, "message": "Error retrieving half gallery images", "error": str(e)}

@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_half_gallery_images_by_id(**kwargs):
    """
    API endpoint to get list of galleryHalf images from a specific service
    """
    service_id = frappe.form_dict.get('service_id')
    if not service_id: frappe.throw(_("Service ID is required"))
    
    try:
        images = _get_images(service_id=service_id, folder_type='galleryHalf')
        images.sort(key=lambda x: x['modified'], reverse=True)
        return {
            "success": True,
            "message": f"Found {len(images)} half gallery images for service: {service_id}" if images else f"No photos found for service: {service_id}",
            "images": images
        }
    except Exception as e:
        frappe.log_error(f"Error in get_half_gallery_images_by_id: {str(e)}")
        return {"success": False, "message": "Error retrieving half gallery images", "error": str(e)}

@frappe.whitelist(allow_guest=True)
@require_viewing_session
def serve_image(**kwargs):
    """
    API endpoint to serve protected images
    """
    service_id = frappe.form_dict.get('service_id')
    folder_type = frappe.form_dict.get('folder_type') 
    image_name = frappe.form_dict.get('image_name')

    if not all([service_id, folder_type, image_name]):
        frappe.throw("Missing required parameters")
    try:
        secure_service_id = secure_filename(service_id)
        secure_folder_type = secure_filename(folder_type)
        secure_name = secure_filename(image_name)
        
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw("Invalid service ID")
        
        if secure_folder_type not in ['gallery', 'galleryHalf']:
            frappe.throw("Invalid folder type.")
        
        if not secure_name:
            frappe.throw("Invalid image name")
        
        private_path = frappe.get_site_path("private", "files", "images")
        image_path = os.path.join(private_path, secure_service_id, secure_folder_type, image_name)
        
        real_image_path = os.path.realpath(image_path)
        real_folder_path = os.path.realpath(os.path.join(private_path, secure_service_id, secure_folder_type))

        if not os.path.exists(real_image_path) or not real_image_path.startswith(real_folder_path + os.sep):
            frappe.throw("Image not found")
        
        if not os.path.isfile(real_image_path):
            frappe.throw("Invalid image file")
        
        mime_type = magic.from_file(real_image_path, mime=True)
        if not mime_type or not mime_type.startswith('image/'):
            frappe.throw("File is not a valid image")
        
        if secure_folder_type == "gallery":
            file_content = add_watermark(real_image_path)
        else:
            with open(real_image_path, 'rb') as f:
                file_content = f.read()
            # file_content = add_watermark_half(real_image_path)
        
        response = Response(
            file_content,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'inline; filename="{secure_name}"',
                'Cache-Control': 'public, max-age=31536000',
                'Content-Length': str(len(file_content)),
                #'Access-Control-Allow-Origin': '*',  # for CORS
                'Access-Control-Allow-Headers': 'Content-Type, X-Session-Token'
            }
        )
        return response
        
    except frappe.DoesNotExistError:
        frappe.local.response.http_status_code = 404
        return {"error": "Image not found"}
    except Exception as e:
        frappe.log_error(f"Error in serve_image: {str(e)}")
        frappe.local.response.http_status_code = 500
        return {"error": "Internal server error", "description":str(e)}

@frappe.whitelist()
def upload_image(service_id, folder_type):
    """
    API endpoint to upload images to the gallery
    """
    try:
        secure_service_id = secure_filename(service_id)
        secure_folder_type = secure_filename(folder_type)
        
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        if secure_folder_type not in ['gallery', 'galleryHalf']:
            frappe.throw(_("Invalid folder type. Must be 'gallery' or 'galleryHalf'"))
        
        if not frappe.request.files:
            frappe.throw(_("No file uploaded"))
        
        uploaded_file = frappe.request.files.get('image')
        if not uploaded_file:
            frappe.throw(_("No image file provided"))
        
        if not uploaded_file.content_type.startswith('image/'):
            frappe.throw(_("File must be an image"))
        
        filename = secure_filename(uploaded_file.filename)
        if not filename:
            frappe.throw(_("Invalid filename"))
        
        private_path = frappe.get_site_path("private", "files", "images")
        folder_path = os.path.join(private_path, secure_service_id, secure_folder_type)
        os.makedirs(folder_path, exist_ok=True)
        
        file_path = os.path.join(folder_path, filename)
        uploaded_file.save(file_path)
        
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "filename": filename,
            "service_id": service_id,
            "folder_type": folder_type,
            "url": f"/api/method/gallery_protection.api.gallery_api.serve_image?service_id={service_id}&folder_type={folder_type}&image_name={filename}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in upload_image: {str(e)}")
        return {"success": False, "message": "Error uploading image", "error": str(e)}

@frappe.whitelist()
def delete_image(service_id, folder_type, image_name):
    """
    API endpoint to delete an image from the gallery
    """
    try:
        secure_service_id = secure_filename(service_id)
        secure_folder_type = secure_filename(folder_type)
        secure_name = secure_filename(image_name)
        
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        if secure_folder_type not in ['gallery', 'galleryHalf']:
            frappe.throw(_("Invalid folder type. Must be 'gallery' or 'galleryHalf'"))
        
        if not secure_name or secure_name != image_name:
            frappe.throw(_("Invalid image name"))
        
        private_path = frappe.get_site_path("private", "files", "images")
        image_path = os.path.join(private_path, secure_service_id, secure_folder_type, image_name)
        
        real_image_path = os.path.realpath(image_path)
        real_folder_path = os.path.realpath(os.path.join(private_path, secure_service_id, secure_folder_type))

        if not os.path.exists(real_image_path) or not real_image_path.startswith(real_folder_path + os.sep):
            frappe.throw("Image not found")
        
        os.remove(real_image_path)
        
        return {
            "success": True,
            "message": "Image deleted successfully",
            "filename": secure_name,
            "service_id": service_id,
            "folder_type": folder_type
        }
        
    except frappe.DoesNotExistError:
        return {"success": False, "message": "Image not found"}
    except Exception as e:
        frappe.log_error(f"Error in delete_image: {str(e)}")
        return {"success": False, "message": "Error deleting image", "error": str(e)}