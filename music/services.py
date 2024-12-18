from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings

def upload_mp3_to_s3(mp3_file, song_name, artist_id, album_id):
    try:
        # Generate a unique file name to avoid conflicts
        mp3_filename = f"{song_name}_{artist_id}_{album_id}.mp3"
        
        # Get the S3 client from settings
        s3_client = settings.S3_CLIENT
        
        # Upload the file to S3
        s3_client.upload_fileobj(
            mp3_file,
            settings.AWS_STORAGE_BUCKET_NAME,
            mp3_filename,
            ExtraArgs={'ContentType': 'audio/mpeg'}
        )
        
        # Generate the S3 file URL
        mp3_url = f"https://d3bghiucejakoj.cloudfront.net/{mp3_filename}"
        
        return mp3_url
    except Exception as e:
        raise Exception(f"Error uploading MP3 to S3: {str(e)}")


# Function to insert song metadata into CockroachDB
def insert_song_metadata(song_name, artist_id, album_id, genre, duration, language, mp3_url):
    try:
        insert_query = """
            INSERT INTO songs (song_name, artist_id, album_id, genre, duration, language, mp3_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        params = [song_name, artist_id, album_id, genre, duration, language, mp3_url]
        
        with connection.cursor() as cursor:
            cursor.execute(insert_query, params)
        
    except Exception as e:
        raise Exception(f"Error saving song data: {str(e)}")



def create_user(email, username, password, isArtist):
    hashed_password = make_password(password)
    query = """
    INSERT INTO "User" (username, email, password, subscription_type, end_date, isArtist)
    VALUES (%s, %s, %s, 'Free', NOW(), %s)
    RETURNING user_id
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [username, email, hashed_password, isArtist])
        user_id = cursor.fetchone()[0]
    return user_id


def authenticate_user(email_or_username, password):
    query = """
    SELECT user_id, email, username, password, isArtist 
    FROM "User"
    WHERE email = %s OR username = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(query, [email_or_username, email_or_username])
        user = cursor.fetchone()
    
    if user:
        user_id, email, username, hashed_password, isArtist = user
        
        # Verify the password
        if check_password(password, hashed_password):  # Use Django's password hashing utilities
            return {
                "id": user_id,
                "email": email,
                "username": username,
                "isArtist": isArtist
            }
    
    return None


def get_song_list():
    with connection.cursor() as cur:
        cur.execute("SELECT song_name, mp3_url FROM Songs;")
        songs = cur.fetchall()
        print(songs)

        song_list = [{"song_name": song[0], "song_url": song[1]} for song in songs]
        # print(song_list)
        return song_list
        
    if song_list:
        return song_list
    else:
        return []
    
# To search for the song to add to listening history
def search_song(song_name):
    with connection.cursor() as cur:
        cur.execute(f"SELECT song_id, song_name, genre, duration, language FROM Songs where song_name = '{song_name}';")
        song = cur.fetchone()
        # print(f"To add song in listening history, found {song_name}.\nDetails: {song}")

        if not song:
            return None
        
        columns = [col[0] for col in cur.description]  # Get column names
        song_data = dict(zip(columns, song))

        if song_data:
            return(song_data)
        else:
            return None
        
# def set_cookie(response, key, value, max_age=3600):
#     """
#     Sets a cookie in the response.
    
#     :param response: The HttpResponse object.
#     :param key: The name of the cookie.
#     :param value: The value of the cookie.
#     :param max_age: Max age of the cookie in seconds (default is 1 hour).
#     """
#     response.set_cookie(key, value, max_age=max_age)
#     return response


# def get_user_cookie(request):
#     # Retrieve the cookie value
#     username = request.COOKIES.get('username', 'Guest')  # Default to 'Guest' if not set
    
#     return username


# # Create a view where you set the cookie
# def set_user_cookie(request):
#     # Call the set_cookie function to set a cookie
#     response = HttpResponse("Cookie has been set!")
#     response = set_cookie(response, 'username', 'john_doe', max_age=3600)  # Cookie for 1 hour
    
#     return response

