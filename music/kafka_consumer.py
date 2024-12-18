from confluent_kafka import Consumer
from cassandra.cluster import Cluster
from datetime import datetime, timedelta
import psycopg2
import json
import uuid

# Configure Kafka consumer
consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'cassandra_consumer_group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_config)
consumer.subscribe(['listening_history', 'playlist_create', 'playlist_delete', 'playlist_add_song', 'playlist_remove_song'])

# Connect to Cassandra
cluster = Cluster(port=9042)
session_db = cluster.connect()
session_db.set_keyspace('audio_streaming_keyspace')

print("Starting Kafka consurmer.")

try:
    while True:
        msg = consumer.poll(1.0)  # Poll Kafka for messages
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        # Parse Kafka message
        event = json.loads(msg.value().decode('utf-8'))
        topic = msg.topic()

        # Handle different topics
        if topic == 'listening_history':
            username = event['username']
            song_id = event['song_id']
            song_name = event['song_name']
            genre = event['genre']
            last_played = datetime.now().isoformat()

            # print(f"Username : {username}, Song id: {song_id}, song_name : {song_name}, genre : {genre}, last_played : {last_played}")

            # Insert into Cassandra
            try:
                session_db.execute(f"""
                    INSERT INTO {username}_listening_history (user_id, song_id, song_name, genre, last_played)
                    VALUES ('123', {uuid.UUID(int=song_id)}, '{song_name}', '{genre}', '{last_played}')
                """)
                print(f"Inserted into {username}_listening_history: {event}")
            except Exception as e:
                print(f"Could not add song to {username}_listening_history.\nError: {e}")

        elif topic == 'playlist_create':
            username = event['username']
            playlist_name = event['playlist_name']
            playlist_table = f"{username}_playlist_{playlist_name.replace(' ', '_')}"

            # Create playlist in Cassandra
            try:
                session_db.execute(f"""
                    INSERT INTO {username}_playlists (playlist_name, creation_date) 
                    VALUES ('{playlist_name}', toTimestamp(now()))
                """)
                print(f"Inserted the {playlist_name} to the list of playlists.")
                
                # session_db.execute(f"""
                #     CREATE TABLE IF NOT EXISTS {playlist_table} (
                #         song_id UUID PRIMARY KEY,
                #         song_name TEXT,
                #         artist_name TEXT,
                #         album_name TEXT,
                #         genre TEXT,
                #         duration INT,
                #         language TEXT
                #     )
                # """)

                session_db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {playlist_table} (
                        song_id UUID,
                        song_name TEXT PRIMARY KEY,
                        genre TEXT,
                        duration INT,
                        language TEXT
                    )
                """)
                print(f"Created playlist '{playlist_name}' for user '{username}'")
            except Exception as e:
                print(f"Error creating playlist '{playlist_name}' for user '{username}': {e}")

        elif topic == 'playlist_delete':
            username = event['username']
            playlist_name = event['playlist_name']
            playlist_table = f"{username}_playlist_{playlist_name.replace(' ', '_')}"

            # Delete playlist in Cassandra
            try:
                session_db.execute(f"DROP TABLE IF EXISTS {playlist_table}")
                session_db.execute(f"""
                    DELETE FROM {username}_playlists WHERE playlist_name='{playlist_name}'
                """)
                print(f"Deleted playlist '{playlist_name}' for user '{username}'")
            except Exception as e:
                print(f"Error deleting playlist '{playlist_name}' for user '{username}': {e}")

        elif topic == 'playlist_add_song':
            username = event['username']
            playlist_name = event['playlist_name']
            song_name = event['song_name']
            genre = event['genre']
            duration = event['duration']
            language = event['language']

            try:
                # Find song details from `song_data`
                # song = session_db.execute(f"SELECT * FROM song_data WHERE title='{song_name}'").one()
                playlist_table = f"{username}_playlist_{playlist_name.replace(' ', '_')}"

                # Add song to the playlist
                session_db.execute(f"""
                    INSERT INTO {playlist_table} (song_id, song_name, genre, duration, language)
                    VALUES ({uuid.UUID(int=123)}, '{song_name}', '{genre}', {int(duration)}, '{language}')
                """)
                print(f"Added song '{song_name}' to playlist '{playlist_name}' for user '{username}'")
            except Exception as e:
                print(f"Error adding song to playlist '{playlist_name}' for user '{username}': {e}")
        elif topic == 'playlist_remove_song':
            username = event['username']
            playlist_name = event['playlist_name']
            song_name = event['song_name']
            playlist_table = f"{username}_playlist_{playlist_name.replace(' ', '_')}"

            try:
                # Remove song from the playlist
                session_db.execute(f"""
                    DELETE FROM {playlist_table} WHERE song_name = '{song_name}';
                """)
                print(f"Deleted song '{song_name}' from playlist '{playlist_name}' for user '{username}'")
            except Exception as e:
                print(f"Error removing song from playlist '{playlist_name}' for user '{username}': {e}")

except KeyboardInterrupt:
    print("Shutting down Kafka consumer.")
finally:
    consumer.close()
