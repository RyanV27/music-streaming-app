from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User,auth
from .services import create_user, authenticate_user, upload_mp3_to_s3, insert_song_metadata, get_song_list

# Create your views here.
def index(request):
    return render(request,'index.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        print(username)
        print(password)
        user = authenticate_user(email_or_username=username, password=password)
        if user:
            print(user)
            return redirect('/')
        else:
            messages.info(request,'Password or Username Mismatch')
            return redirect('login')
    else:
        return render(request,'login.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        isArtist = request.POST['isArtist']

        if password==password2:
            # if User.objects.filter(email=email).exists():
            #     messages.info(request,'Email already exists.')
            #     return redirect('signup')
            # elif User.objects.filter(username=username).exists():
            #     messages.info(request,'Username already taken.')
            #     return redirect('signup')
            # else:
            user_id = create_user(email, username, password, isArtist)

            user = authenticate_user(email_or_username=username, password=password)
            # auth.login(request,user_login)
            if user:
                print(user)
            return redirect('/')
        else:
            messages.info(request,'Password Not Matching.')
            return redirect('signup')
    else:
        return render(request,'signup.html')

def logout(request):
    pass


# def upload(request):
#     if request.method == 'POST':
#         # Retrieve form data
#         song_name = request.POST['song_name']
#         artist_id = request.POST['artist_id']
#         album_id = request.POST['album_id']
#         genre = request.POST['genre']
#         duration = request.POST['duration']
#         language = request.POST['language']

#         mp3_file = request.FILES['mp3_file']
#         try:
#             # Step 1: Upload MP3 to S3
#             mp3_url = upload_mp3_to_s3(mp3_file, song_name, artist_id, album_id)
        
#             # Step 2: Insert song metadata into CockroachDB
#             insert_song_metadata(song_name, artist_id, album_id, genre, duration, language, mp3_url)
#             return HttpResponse("Song uploaded successfully!", status=200)
#         except Exception as e:
#             return HttpResponse(f"Error: {str(e)}", status=500)
#     return render(request, 'upload.html')


def upload(request):
    if request.method == 'POST':
        # Retrieve form data
        song_name = request.POST['song_name']
        artist_id = request.POST['artist_id']
        album_id = request.POST['album_id']
        genre = request.POST['genre']
        duration = request.POST['duration']
        language = request.POST['language']

        mp3_file = request.FILES['mp3_file']
        try:
            # Step 1: Upload MP3 to S3
            mp3_url = upload_mp3_to_s3(mp3_file, song_name, artist_id, album_id)
        
            # Step 2: Insert song metadata into CockroachDB
            insert_song_metadata(song_name, artist_id, album_id, genre, duration, language, mp3_url)

            # Render success page
            return render(request, 'templates/upload_success.html', {'song_name': song_name})
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", status=500)
    return render(request, 'upload.html')


def music(request):
    return render(request,'music.html')


def songs_view(request):
    try:
        song_list = get_song_list()     
        return render(request, 'songs_list.html', {'songs': song_list}) 
    except Exception as e:
        print(f"Error fetching songs: {e}")
        return render(request, 'songs_list.html', {'error': 'Error fetching songs from the database.'})

