from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Main Views
    path('', views.gallery, name='gallery'),
    path('upload/', views.upload, name='upload'),
    path('chat/', views.chat_list, name='chat'),
    path('chat/<int:conversation_id>/', views.chat_detail, name='chat_detail'),
    path('register/', views.register, name='register'),
    path('logout/', LogoutView.as_view(next_page='gallery'), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    
    # User / Profile Views
    path('profile/<str:username>/', views.user_profile, name='profile'),
    path('follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    
    # Photo Actions
    path('photo/<int:photo_id>/like/', views.toggle_like, name='toggle_like'),
    path('photo/<int:photo_id>/view/', views.view_photo, name='view_photo'),
    path('photo/<int:photo_id>/comment/', views.add_comment, name='add_comment'),
    path('photo/<int:photo_id>/modal/', views.get_post_detail, name='get_post_detail'),
]