import json
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from .forms import UserRegisterForm
from .models import Profile, Photo, Like, Comment, Conversation, Message


# --- UPLOAD MODAL API ---
def upload_modal_api(request):
    if request.method == 'POST' and request.user.is_authenticated:
        file = request.FILES.get('file')
        title = request.POST.get('title', '')

        if not file:
            return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)

        # Smart video detection
        is_video = (
            file.content_type.startswith('video/') or 
            file.name.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv'))
        )

        if is_video:
            photo = Photo.objects.create(uploader=request.user, title=title, video=file)
        else:
            photo = Photo.objects.create(uploader=request.user, title=title, image=file)

        return JsonResponse({'success': True, 'photo_id': photo.id})

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


# --- 1. HOME GALLERY VIEW ---
def gallery(request):
    """Fetches photos with dynamic tab filtering and AJAX paginated infinite scroll."""
    active_tab = request.GET.get('tab', 'foryou')
    page_number = request.GET.get('page', 1)
    live_photos = Photo.objects.all()[:5]

    if active_tab == 'popular':
        photos_list = Photo.objects.annotate(likes_count=models.Count('like')).order_by('-likes_count', '-views', '-created_at')
    elif active_tab == 'following':
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            following_profiles = request.user.profile.following.all()
            photos_list = Photo.objects.filter(uploader__profile__in=following_profiles).order_by('-created_at')
        else:
            photos_list = Photo.objects.none()
    else:
        active_tab = 'foryou'
        photos_list = Photo.objects.all().order_by('-created_at')

    paginator = Paginator(photos_list, 12)  # Loads 12 photos per page batch
    photos = paginator.get_page(page_number)

    # Return partial card HTML fragment for AJAX infinite scroll requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/photo_cards.html', {'photos': photos})

    return render(request, 'gallery.html', {
        'live_photos': live_photos,
        'photos': photos,
        'active_tab': active_tab
    })


# --- 2. UPLOAD PHOTO ---
@login_required
def upload(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        file = request.FILES.get('file') or request.FILES.get('image')
        
        if file:
            is_video = (
                file.content_type.startswith('video/') or 
                file.name.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv'))
            )

            if is_video:
                Photo.objects.create(title=title, video=file, uploader=request.user)
            else:
                Photo.objects.create(title=title, image=file, uploader=request.user)
                
            return redirect('gallery')
            
    return render(request, 'upload.html')


# --- 3. CHAT LIST PAGE VIEW ---
@login_required
def chat_list(request):
    saved_convo = request.user.conversations.annotate(num_parts=models.Count('participants')).filter(num_parts=1).first()
    if not saved_convo:
        saved_convo = Conversation.objects.create()
        saved_convo.participants.add(request.user)
        
    other_conversations = request.user.conversations.annotate(num_parts=models.Count('participants')).filter(num_parts__gt=1).order_by('-updated_at')
    conversations = [saved_convo] + list(other_conversations)
    online_friends = request.user.profile.followers.filter(user__is_active=True)[:6] if hasattr(request.user, 'profile') else []

    return render(request, 'chat.html', {
        'conversations': conversations,
        'saved_convo_id': saved_convo.id,
        'online_friends': online_friends
    })


# --- 4. CHAT DETAIL THREAD VIEW ---
@login_required
def chat_detail(request, conversation_id):
    conversation = get_object_or_404(request.user.conversations, id=conversation_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.save()
            return redirect('chat_detail', conversation_id=conversation.id)
            
    saved_convo = request.user.conversations.annotate(num_parts=models.Count('participants')).filter(num_parts=1).first()
    if not saved_convo:
        saved_convo = Conversation.objects.create()
        saved_convo.participants.add(request.user)
        
    other_conversations = request.user.conversations.annotate(num_parts=models.Count('participants')).filter(num_parts__gt=1).order_by('-updated_at')
    conversations = [saved_convo] + list(other_conversations)
    
    messages = conversation.messages.all()
    online_friends = request.user.profile.followers.filter(user__is_active=True)[:6] if hasattr(request.user, 'profile') else []

    return render(request, 'chat.html', {
        'conversations': conversations,
        'active_conversation': conversation,
        'saved_convo_id': saved_convo.id,
        'messages': messages,
        'online_friends': online_friends
    })


# --- 5. LIKE LOGIC ---
@login_required
@require_POST
def toggle_like(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    like, created = Like.objects.get_or_create(user=request.user, photo=photo)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'total_likes': Like.objects.filter(photo=photo).count()
    })


# --- 6. POST MODAL VIEW ---
def post_modal_view(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    
    photo.views += 1
    photo.save(update_fields=['views'])
    
    is_liked = Like.objects.filter(photo=photo, user=request.user).exists() if request.user.is_authenticated else False
    
    if hasattr(photo, 'comments'):
        comments = photo.comments.all().order_by('-created_at')
    else:
        comments = photo.comment_set.all().order_by('-created_at')
    
    return render(request, 'partials/post_modal.html', {
        'photo': photo, 
        'comments': comments,
        'is_liked': is_liked,
    })


# --- 7. VIEW TRACKER ---
def view_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    photo.views += 1
    photo.save()
    return JsonResponse({'status': 'updated', 'views': photo.views})


# --- 8. POP-UP MODAL CONTENT (AJAX) ---
def get_post_detail(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)
    return render(request, 'partials/post_modal_content.html', {'photo': photo})


# --- 9. SUBMIT COMMENT (AJAX) ---
@login_required
def add_comment(request, photo_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        photo = get_object_or_404(Photo, id=photo_id)
        
        if data.get('content'):
            comment = Comment.objects.create(
                author=request.user,
                photo=photo,
                content=data['content']
            )
            return JsonResponse({
                'status': 'success',
                'comment_author': comment.author.username,
                'comment_content': comment.content,
                'comment_avatar_url': comment.author.profile.avatar.url if hasattr(comment.author, 'profile') and comment.author.profile.avatar else None,
            })
    return JsonResponse({'status': 'error'})


# --- 10. REGISTRATION ---
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # UserRegisterForm handles hashing securely out of the box
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f"Welcome to Clubb, {user.username}!")
            return redirect('gallery')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()
        
    # Corrected path pointing directly to your registration/ folder structure
    return render(request, 'registration/register.html', {'form': form})


# --- 11. PROFILE ---
def user_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)
    user_photos = Photo.objects.filter(uploader=target_user).order_by('-created_at')
    
    is_following = False
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        is_following = target_profile in request.user.profile.following.all()

    return render(request, 'profile.html', {
        'target_user': target_user,
        'target_profile': target_profile,
        'photos': user_photos,
        'is_following': is_following,
        'posts_count': user_photos.count(),
        'followers_count': target_profile.followers.count(),
        'following_count': target_profile.following.count(),
    })
 

# --- 12. FOLLOW MECHANIC ---
@login_required
def toggle_follow(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    profile = request.user.profile
    if user_to_follow.profile in profile.following.all():
        profile.following.remove(user_to_follow.profile)
        action = "unfollowed"
    else:
        profile.following.add(user_to_follow.profile)
        action = "followed"
    return JsonResponse({'action': action, 'follower_count': user_to_follow.profile.followers.count()})