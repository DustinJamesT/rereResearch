# Import the Cloudinary libraries
# ==============================
import cloudinary
import cloudinary.uploader
import cloudinary.api

import os 

# Import to format the JSON responses
# ==============================
import json

# Set configuration parameter: return "https" URLs by setting secure=True  
# ==============================

cloudinary.config(cloud_name = os.getenv('CLOUD_NAME'), api_key=os.getenv('API_KEY'), api_secret=os.getenv('API_SECRET'), secure = True)

#config = cloudinary.config(secure=True)


def uploadImage(filepath, filename):

  # Upload the image and get its URL
  # ==============================

  # Upload the image.
  # Set the asset's public ID and allow overwriting the asset with new versions
  cloudinary.uploader.upload(filepath, public_id= filename, unique_filename = False, overwrite=True, folder = 'messari-charts', use_filename=True)

  # Build the URL for the image and save it in the variable 'srcURL'
  srcURL = cloudinary.CloudinaryImage(filename).build_url()

  return srcURL