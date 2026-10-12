from django.contrib import admin
# Change 'Album' to 'Collection' and add 'Profile' and 'Like'
from .models import Photo, Collection, Profile, Like

# Register the new models so you can see them in the admin panel
admin.site.register(Photo)
admin.site.register(Collection)
admin.site.register(Profile)
admin.site.register(Like)