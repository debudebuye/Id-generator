"""
Integration script to add image upload handling to routes.py
Run this script to automatically update your routes file
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path

def add_image_handling_to_routes():
    """Add image handling code to routes.py"""
    routes_file = 'app/routes.py'
    
    if not os.path.exists(routes_file):
        print(f"✗ Error: {routes_file} not found")
        return False
    
    # Backup original file
    backup_file(routes_file)
    
    # Read the file
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already integrated
    if 'handle_cropped_images_in_generate_id' in content:
        print("✓ Image handling already integrated")
        return True
    
    # Add import at the top
    import_line = "from .routes_image_handler import handle_cropped_images_in_generate_id, save_cropped_image\n"
    
    # Find the imports section
    if 'from .services.id_card_service import IDCardService' in content:
        content = content.replace(
            'from .services.id_card_service import IDCardService',
            'from .services.id_card_service import IDCardService\n' + import_line
        )
    else:
        # Add after other imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from .'):
                lines.insert(i + 1, import_line.strip())
                break
        content = '\n'.join(lines)
    
    # Add image handling in generate_id function
    # Find the line after FIN validation
    search_text = 'fin_number = f"{clean_fin[:4]}-{clean_fin[4:8]}-{clean_fin[8:12]}"'
    
    if search_text in content:
        image_handling_code = '''
    
    # Handle cropped images from form
    try:
        uploaded_images = handle_cropped_images_in_generate_id()
        print(f"✓ Processed uploaded images: {uploaded_images}")
    except Exception as img_error:
        print(f"⚠ Error processing images: {img_error}")
        uploaded_images = {'photo': None, 'front': None, 'back': None}
'''
        
        content = content.replace(
            search_text,
            search_text + image_handling_code
        )
    
    # Write updated content
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Successfully updated {routes_file}")
    return True

def replace_index_template():
    """Replace index.html with updated version"""
    old_index = 'app/templates/index.html'
    new_index = 'app/templates/index_updated.html'
    
    if not os.path.exists(new_index):
        print(f"✗ Error: {new_index} not found")
        return False
    
    if os.path.exists(old_index):
        # Backup original
        backup_file(old_index)
    
    # Copy new version
    shutil.copy2(new_index, old_index)
    print(f"✓ Replaced {old_index} with updated version")
    return True

def main():
    """Main integration function"""
    print("=" * 60)
    print("Image Upload Integration Script")
    print("=" * 60)
    print()
    
    print("Step 1: Updating routes.py...")
    if add_image_handling_to_routes():
        print("✓ Routes updated successfully")
    else:
        print("✗ Failed to update routes")
        return
    
    print()
    print("Step 2: Replacing index.html...")
    if replace_index_template():
        print("✓ Index template updated successfully")
    else:
        print("✗ Failed to update index template")
        return
    
    print()
    print("=" * 60)
    print("✓ Integration Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the changes in app/routes.py")
    print("2. Test the new index page")
    print("3. Check that images are being saved correctly")
    print("4. Integrate saved images with ID generation")
    print()
    print("Backup files have been created with timestamp suffix")
    print("You can restore them if needed")

if __name__ == '__main__':
    main()
