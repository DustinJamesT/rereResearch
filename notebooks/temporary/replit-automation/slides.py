# -- wrapper for using replid database 

from replit import db

def add_image(name, url):
    db[name] = {
        'report': '', 
        'subsection': '',
        'days': 0,
        'url': url
    }

# -- returns dict of all images in database containing report in name
# ----- wish there was a better way to search inside of rows in database
def get_report_images(report): 
    # -- loop through all images in database and save those with matching report 
    images = {}
    for key in db.keys():
        if report in db[key]['report']:
            images[key] = db[key]
    
    return images