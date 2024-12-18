from confluent_kafka import Producer
from datetime import timedelta
import json

# Configure Kafka producer
kafka_config = {
    'bootstrap.servers': 'localhost:9092'  # Adjust based on your Kafka setup
}
producer = Producer(kafka_config)

# Callback for delivery reports
def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def send_song_to_kafka(song_details):
    # Create the song message
    # message = {
    #     "song_name": song_name,
    #     "song_url": song_url
    # }

    song_details['duration'] = song_details['duration'].total_seconds()
    serialized_value = json.dumps(song_details)

    # Send the message to the 'song-clicks' topic in Kafka
    producer.produce('listening_history', value=serialized_value.encode('utf-8'))
    producer.flush()  # Ensure the message is sent immediately

def create_playlist_kafka(playlist_details):
    serialized_value = json.dumps(playlist_details)
    producer.produce('playlist_create', value=serialized_value.encode('utf-8'))
    producer.flush() 

def delete_playlist_kafka(playlist_details):
    serialized_value = json.dumps(playlist_details)
    producer.produce('playlist_delete', value=serialized_value.encode('utf-8'))
    producer.flush()

def add_playlist_song_kafka(song_details):
    song_details['duration'] = song_details['duration'].total_seconds()
    serialized_value = json.dumps(song_details)
    producer.produce('playlist_add_song', value=serialized_value.encode('utf-8'))
    producer.flush()

def remove_playlist_song_kafka(song_details):
    serialized_value = json.dumps(song_details)
    producer.produce('playlist_remove_song', value=serialized_value.encode('utf-8'))
    producer.flush()