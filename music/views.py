from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User,auth
from .services import create_user, authenticate_user, upload_mp3_to_s3, insert_song_metadata, get_song_list, search_song
from .kafka_producer import delivery_report, send_song_to_kafka, create_playlist_kafka, delete_playlist_kafka, add_playlist_song_kafka, remove_playlist_song_kafka
import json

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime, timedelta
import uuid

cluster = Cluster(port=9042)
session_db = cluster.connect()
session_db.set_keyspace('audio_streaming_keyspace')

# Create your views here.
def index(request):
    username = request.session.get('username', 'Guest')  # Default to 'Guest' if not set
    return render(request,'index.html', {'username': username})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        print(username)
        print(password)
        user = authenticate_user(email_or_username=username, password=password)
        if user:
            request.session['username'] = username
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

            # Commands for Cassandra
            try:
                session_db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {username}_playlists (playlist_name TEXT, creation_date TIMESTAMP, PRIMARY KEY (playlist_name))
                """)
                session_db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {username}_listening_history (user_id TEXT, song_id UUID, song_name TEXT, genre TEXT, last_played TIMESTAMP, PRIMARY KEY (user_id, last_played))
                """)
            except:
                messages.info(request,'Listening history and Playlists table not created.')

            if user:
                print(user)
                request.session['username'] = username
            return redirect('/')
        else:
            messages.info(request,'Password Not Matching.')
            return redirect('signup')
    else:
        return render(request,'signup.html')

def logout(request):
    request.session['username'] = 'guest'
    return redirect('login')

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
    
def notify_song_click(request):
    if request.method == 'POST':
        # Get the song details from the AJAX request body
        data = json.loads(request.body)
        song_name = data.get('song_name')
        song_url = data.get('song_url')

        username = request.session.get("username")

        song_details = search_song(song_name)

        if not song_details:
            return HttpResponse('Song details not found!')

        # Adding username to details
        song_details['username'] = username

        # Send the song details to Kafka
        send_song_to_kafka(song_details)

        # Return a success response
        return HttpResponse('Song details sent to Kafka successfully!')


def listening_history(request):
    history = None
    try:
        username = request.session.get("username")
        
        history = session_db.execute(f"""
            SELECT * FROM {username}_listening_history WHERE user_id = '123' ORDER BY last_played DESC;
        """)

    except Exception as e:
        print(f"Error in retrieving lisening_history songs: {e}")

    return render(request, 'listening_history.html', {"username" : username, "history" : history})

def list_playlists(request):
    username = request.session.get("username")

    try:
        playlists = session_db.execute(f"SELECT * FROM {username}_playlists;")
        # return render_template('playlists.html', playlists=playlists)
        return render(request, 'playlists.html', {"username" : username, "playlists" : playlists})
    except Exception as e:
        print(f"Error fetching playlists: {e}")
        return HttpResponse('Error fetching playlists!')
    
def create_playlist(request):    
    username = request.session['username']
    playlist_name = request.POST.get('playlist_name')

    if not playlist_name:
        messages.error(request, "Playlist name is required.")
        return redirect('playlists')  
    
    try:
        # Insert playlist into user's playlists table
        # session_db.execute(f"""
        #     INSERT INTO {username}_playlists (playlist_name, creation_date) 
        #     VALUES ('{playlist_name}', toTimestamp(now()))
        # """)

        create_playlist_kafka({"username" : username, "playlist_name" : playlist_name})

        messages.success(request, f"{playlist_name} playlist created successfully!")
        return redirect('playlists')
    except Exception as e:
        return redirect('playlists')
    
def delete_playlist(request):    
    username = request.session['username']
    playlist_name = request.POST.get('playlist_name')

    if not playlist_name:
        messages.error(request, "Playlist name is required.")
        return redirect('playlists')  
    
    try:
        delete_playlist_kafka({"username" : username, "playlist_name" : playlist_name})

        messages.success(request, f"Playlist deleted successfully!")
        return redirect('playlists')
    except Exception as e:
        return redirect('playlists')
    
def list_playlist_songs(request, playlist_name):
    username = request.session['username']
    playlist_table = f"{username}_playlist_{playlist_name.replace(' ', '_')}"
    print(f"Playlist table name : {playlist_table}")
        
    try:
        songs = session_db.execute(f"SELECT * FROM {playlist_table};")
        songs = [dict(row) for row in songs] 

        print(f"Songs in the {playlist_table}:-")
        for row in songs:
            print(row)
    except Exception as e:
        print("Failed to load playlist songs page!")
        # return HttpResponse("Failed to load playlist songs page!")

    return render(request, 'playlist_songs.html', {"playlist_name" : playlist_name, "songs" : songs})

def add_playlist_song(request, playlist_name):
    username = request.session['username']
    song_name = request.POST.get('song_name')
    # print(f"Song name : {song_name}")

    song_details = search_song(song_name)
    # print(f"Song details : {song_details}")

    if not song_details:
        # print(f"{song_name} details not found.")
        messages.error(request, "Song could not be found.")
        return redirect(f'/playlists/{playlist_name}')
    else:
        print(f"{song_name} details found.")
    
    song_details['username'] = username
    song_details['playlist_name'] = playlist_name

    try:
        # print(f"Sending song details to kafka.\nDetails: {song_details}")
        add_playlist_song_kafka(song_details)

        messages.success(request, f"Successfully added {song_name} to {playlist_name} playlist !")
        return redirect(f'/playlists/{playlist_name}')
    except Exception as e:
        print(f"Failed to add {song_name} to {playlist_name} playlist.")
        return redirect(f'/playlists/{playlist_name}')

def remove_playlist_song(request, playlist_name):
    username = request.session['username']
    song_name = request.POST.get('song_name')

    song_details = {"username" : username, "playlist_name" : playlist_name, "song_name" : song_name}
    
    try:
        # print(f"Sending song details to kafka.\nDetails: {song_details}")
        remove_playlist_song_kafka(song_details)

        messages.success(request, f"Successfully removed {song_name} from {playlist_name} playlist !")
        return redirect(f'/playlists/{playlist_name}')
    except Exception as e:
        print(f"Failed to remove {song_name} from {playlist_name} playlist.")
        return redirect(f'/playlists/{playlist_name}')