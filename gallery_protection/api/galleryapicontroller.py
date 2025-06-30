import frappe
import os
from frappe import _
from frappe.utils.file_manager import get_file_path
from werkzeug.wrappers import Response
from werkzeug.utils import secure_filename
import mimetypes
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def require_viewing_session(method):
    """
    Decorator to require viewing session for gallery endpoints
    """
    def wrapper(*args, **kwargs):
        try:
            # Get session token from request
            session_token = frappe.get_request_header("X-Session-Token")
            
            if not session_token:
                frappe.throw(_("Missing session token in headers"))
            
            # Import session validation (assuming session code is in session_manager.py)
            from .session_manager import validate_viewing_session, increment_session_usage
            
            # Validate session
            validation_result = validate_viewing_session(session_token)
            if not validation_result.get("valid"):
                return {
                    "success": False,
                    "error": "Session validation failed",
                    "message": validation_result.get("message")
                }

            return method(*args, **kwargs)
            
            # # Increment usage counter
            # increment_session_usage(session_token)
            
            # # Call original function
            # return func(*args, **kwargs)
            
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


@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_all_gallery_images(cmd=None):
    """
    API endpoint to get list of all gallery images from all services
    Requires authentication via ERPNext
    """
    
    try:
        # Get the private files directory path
        private_path = frappe.get_site_path("private", "files", "images")
        
        # Check if files directory exists
        if not os.path.exists(private_path):
            return {
                "success": False,
                "message": "Files directory not found",
                "images": []
            }
        
        # Get all image files from all service/gallery folders
        supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        images = []
        
        # Iterate through all service directories
        # frappe.logger().info(f"startt:: ")
        
        for service_name in os.listdir(private_path):
            service_path = os.path.join(private_path, service_name)
            
            # Check if it's a directory
            if not os.path.isdir(service_path):
                continue
                
            gallery_path = os.path.join(service_path, "gallery")
            # frappe.logger().info(f"Checking service: {service_name} | gallery_path: {gallery_path}")
            # print(f"gallery: {gallery_path} service: {service_name} and {service_path} ||| private : {private_path}")
            
            # Check if gallery directory exists
            if not os.path.exists(gallery_path):
                continue
            
            # Get all image files from this gallery
            for filename in os.listdir(gallery_path):
                if any(filename.lower().endswith(ext) for ext in supported_formats):
                    file_path = os.path.join(gallery_path, filename)
                    if os.path.isfile(file_path):
                        file_stat = os.stat(file_path)
                        
                        images.append({
                            "name": filename,
                            "service_id": service_name,
                            "size": file_stat.st_size,
                            "modified": file_stat.st_mtime,
                            "url": f"/api/method/gallery_protection.api.galleryapicontroller.serve_image?service_id={service_name}&folder_type=gallery&image_name={filename}"
                        })
        
        # Sort by modification time (newest first)
        # images.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(images)} images",
            "images": images
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_all_gallery_images: {str(e)}")
        return {
            "success": False,
            "message": "Error retrieving gallery images",
            "error": str(e)
        }
    


@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_gallery_images_by_id(**kwargs):
    """
    API endpoint to get list of gallery images from a specific service
    Requires authentication via ERPNext
    """
    service_id = frappe.form_dict.get('service_id')
    if not service_id: frappe.throw(_("Service ID is required"))
    try:
        # Validate and secure the service_id
        secure_service_id = secure_filename(service_id)
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        # Get the private files directory path
        private_path = frappe.get_site_path("private", "files", "images")
        gallery_path = os.path.join(private_path, secure_service_id, "gallery")
        
        # Check if gallery directory exists
        if not os.path.exists(gallery_path):
            return {
                "success": True,
                "message": f"No photos found for service: {service_id}",
                "images": []
            }
        
        # Get all image files
        supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        images = []
        
        for filename in os.listdir(gallery_path):
            if any(filename.lower().endswith(ext) for ext in supported_formats):
                file_path = os.path.join(gallery_path, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    
                    images.append({
                        "name": filename,
                        "service_id": service_id,
                        "size": file_stat.st_size,
                        "modified": file_stat.st_mtime,
                        "url": f"/api/method/gallery_protection.api.galleryapicontroller.serve_image?service_id={service_id}&folder_type=gallery&image_name={filename}"
                    })
        
        # Sort by modification time (newest first)
        images.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(images)} images for service: {service_id}" if images else f"No photos found for service: {service_id}",
            "images": images
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_gallery_images_by_id: {str(e)}")
        return {
            "success": False,
            "message": "Error retrieving gallery images",
            "error": str(e)
        }
    


@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_all_half_gallery_images(cmd=None):
    """
    API endpoint to get list of all galleryHalf images from all services
    Requires authentication via ERPNext
    """
    try:
        # Get the private files directory path
        private_path = frappe.get_site_path("private", "files", "images")
        
        # Check if files directory exists
        if not os.path.exists(private_path):
            return {
                "success": False,
                "message": "Files directory not found",
                "images": []
            }
        
        # Get all image files from all service/galleryHalf folders
        supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        images = []
        
        # Iterate through all service directories
        for service_name in os.listdir(private_path):
            service_path = os.path.join(private_path, service_name)
            
            # Check if it's a directory
            if not os.path.isdir(service_path):
                continue
                
            gallery_half_path = os.path.join(service_path, "galleryHalf")
            
            # Check if galleryHalf directory exists
            if not os.path.exists(gallery_half_path):
                continue
            
            # Get all image files from this galleryHalf
            for filename in os.listdir(gallery_half_path):
                if any(filename.lower().endswith(ext) for ext in supported_formats):
                    file_path = os.path.join(gallery_half_path, filename)
                    if os.path.isfile(file_path):
                        file_stat = os.stat(file_path)
                        
                        images.append({
                            "name": filename,
                            "service_id": service_name,
                            "size": file_stat.st_size,
                            "modified": file_stat.st_mtime,
                            "url": f"/api/method/gallery_protection.api.galleryapicontroller.serve_image?service_id={service_name}&folder_type=galleryHalf&image_name={filename}"
                        })
        
        # Sort by modification time (newest first)
        images.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(images)} half gallery images",
            "images": images
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_all_half_gallery_images: {str(e)}")
        return {
            "success": False,
            "message": "Error retrieving half gallery images",
            "error": str(e)
        }
    


@frappe.whitelist(allow_guest=True)
@require_viewing_session
def get_half_gallery_images_by_id(**kwargs):
    """
    API endpoint to get list of galleryHalf images from a specific service
    Requires authentication via ERPNext
    """
    service_id = frappe.form_dict.get('service_id')
    if not service_id: frappe.throw(_("Service ID is required"))
    try:
        # Validate and secure the service_id
        secure_service_id = secure_filename(service_id)
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        # Get the private files directory path
        private_path = frappe.get_site_path("private", "files", "images")
        gallery_half_path = os.path.join(private_path, secure_service_id, "galleryHalf")
        
        # Check if galleryHalf directory exists
        if not os.path.exists(gallery_half_path):
            return {
                "success": True,
                "message": f"No photos found for service: {service_id}",
                "images": []
            }
        
        # Get all image files
        supported_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        images = []
        
        for filename in os.listdir(gallery_half_path):
            if any(filename.lower().endswith(ext) for ext in supported_formats):
                file_path = os.path.join(gallery_half_path, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    
                    images.append({
                        "name": filename,
                        "service_id": service_id,
                        "size": file_stat.st_size,
                        "modified": file_stat.st_mtime,
                        "url": f"/api/method/gallery_protection.api.galleryapicontroller.serve_image?service_id={service_id}&folder_type=galleryHalf&image_name={filename}"
                    })
        
        # Sort by modification time (newest first)
        images.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(images)} half gallery images for service: {service_id}" if images else f"No photos found for service: {service_id}",
            "images": images
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_half_gallery_images_by_id: {str(e)}")
        return {
            "success": False,
            "message": "Error retrieving half gallery images",
            "error": str(e)
        }
    


@frappe.whitelist(allow_guest=True)
@require_viewing_session
def serve_image():
    """
    API endpoint to serve protected images
    Requires authentication via ERPNext
    """
    service_id = frappe.form_dict.get('service_id')
    folder_type = frappe.form_dict.get('folder_type') 
    image_name = frappe.form_dict.get('image_name')

    if not all([service_id, folder_type, image_name]):
        frappe.throw(_("Missing required parameters"))
    try:
        # Validate and secure the parameters
        secure_service_id = secure_filename(service_id)
        secure_folder_type = secure_filename(folder_type)
        secure_name = secure_filename(image_name)
        
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        if not secure_folder_type or secure_folder_type != folder_type:
            frappe.throw(_("Invalid folder type"))
            
        if secure_folder_type not in ['gallery', 'galleryHalf']:
            frappe.throw(_("Invalid folder type. Must be 'gallery' or 'galleryHalf'"))
        
        if not secure_name or secure_name != image_name:
            frappe.throw(_("Invalid image name"))
        
        # Get the private files directory path
        private_path = frappe.get_site_path("private", "files")
        service_path = os.path.join(private_path, secure_service_id)
        folder_path = os.path.join(service_path, secure_folder_type)
        image_path = os.path.join(folder_path, secure_name)
        
        # Check if file exists and is within the correct directory
        if not os.path.exists(image_path) or not os.path.commonpath([folder_path, image_path]) == folder_path:
            frappe.throw(_("Image not found"), frappe.DoesNotExistError)
        
        # Check if it's actually a file (not directory)
        if not os.path.isfile(image_path):
            frappe.throw(_("Invalid image file"))
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith('image/'):
            frappe.throw(_("File is not a valid image"))
        
        # Read and serve the file
        with open(image_path, 'rb') as f:
            file_content = f.read()
        
        # Create response with proper headers
        response = Response(
            file_content,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'inline; filename="{secure_name}"',
                'Cache-Control': 'public, max-age=31536000',  # Cache for 1 year
                'Content-Length': str(len(file_content))
            }
        )
        
        return response
        
    except frappe.DoesNotExistError:
        frappe.local.response.http_status_code = 404
        return {"error": "Image not found"}
    except Exception as e:
        frappe.log_error(f"Error in serve_image: {str(e)}")
        frappe.local.response.http_status_code = 500
        return {"error": "Internal server error"}


@frappe.whitelist()
def upload_image(service_id, folder_type):
    """
    API endpoint to upload images to the gallery
    Requires authentication via ERPNext
    """
    try:
        # Validate and secure the parameters
        secure_service_id = secure_filename(service_id)
        secure_folder_type = secure_filename(folder_type)
        
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        if not secure_folder_type or secure_folder_type != folder_type:
            frappe.throw(_("Invalid folder type"))
            
        if secure_folder_type not in ['gallery', 'galleryHalf']:
            frappe.throw(_("Invalid folder type. Must be 'gallery' or 'galleryHalf'"))
        
        # Check if file was uploaded
        if not frappe.request.files:
            frappe.throw(_("No file uploaded"))
        
        uploaded_file = frappe.request.files.get('image')
        if not uploaded_file:
            frappe.throw(_("No image file provided"))
        
        # Validate file type
        if not uploaded_file.content_type.startswith('image/'):
            frappe.throw(_("File must be an image"))
        
        # Secure filename
        filename = secure_filename(uploaded_file.filename)
        if not filename:
            frappe.throw(_("Invalid filename"))
        
        # Ensure directory structure exists
        private_path = frappe.get_site_path("private", "files")
        service_path = os.path.join(private_path, secure_service_id)
        folder_path = os.path.join(service_path, secure_folder_type)
        os.makedirs(folder_path, exist_ok=True)
        
        # Save file
        file_path = os.path.join(folder_path, filename)
        uploaded_file.save(file_path)
        
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "filename": filename,
            "service_id": service_id,
            "folder_type": folder_type,
            "url": f"/api/method/gallery_protection.api.galleryapicontroller.serve_image?service_id={service_id}&folder_type={folder_type}&image_name={filename}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error in upload_image: {str(e)}")
        return {
            "success": False,
            "message": "Error uploading image",
            "error": str(e)
        }

@frappe.whitelist()
def delete_image(service_id, folder_type, image_name):
    """
    API endpoint to delete an image from the gallery
    Requires authentication via ERPNext
    """
    try:
        # Validate and secure the parameters
        secure_service_id = secure_filename(service_id)
        secure_folder_type = secure_filename(folder_type)
        secure_name = secure_filename(image_name)
        
        if not secure_service_id or secure_service_id != service_id:
            frappe.throw(_("Invalid service ID"))
        
        if not secure_folder_type or secure_folder_type != folder_type:
            frappe.throw(_("Invalid folder type"))
            
        if secure_folder_type not in ['gallery', 'galleryHalf']:
            frappe.throw(_("Invalid folder type. Must be 'gallery' or 'galleryHalf'"))
        
        if not secure_name or secure_name != image_name:
            frappe.throw(_("Invalid image name"))
        
        # Get the private files directory path
        private_path = frappe.get_site_path("private", "files")
        service_path = os.path.join(private_path, secure_service_id)
        folder_path = os.path.join(service_path, secure_folder_type)
        image_path = os.path.join(folder_path, secure_name)
        
        # Check if file exists and is within the correct directory
        if not os.path.exists(image_path) or not os.path.commonpath([folder_path, image_path]) == folder_path:
            frappe.throw(_("Image not found"), frappe.DoesNotExistError)
        
        # Delete the file
        os.remove(image_path)
        
        return {
            "success": True,
            "message": "Image deleted successfully",
            "filename": secure_name,
            "service_id": service_id,
            "folder_type": folder_type
        }
        
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": "Image not found"
        }
    except Exception as e:
        frappe.log_error(f"Error in delete_image: {str(e)}")
        return {
            "success": False,
            "message": "Error deleting image",
            "error": str(e)
        }
