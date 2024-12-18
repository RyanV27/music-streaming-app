# Audio Streaming Service

## Introduction
With the rise of digital content consumption, music streaming platforms have become an integral part of daily life, providing vast music libraries, personalized recommendations, and seamless user access. This project implements a hybrid architecture leveraging distributed database systems to handle real-time music streaming, combining scalability, fault tolerance, and performance optimization.

## Features
- **Scalable Architecture**: Designed to handle millions of users simultaneously.
- **Hybrid Database System**:
  - **Cassandra**: Manages user interaction data such as playlists and listening history.
  - **CockroachDB**: Handles structured metadata like song, artist, and album details.
- **Real-Time Data Processing**: Ensures low-latency music streaming.
- **Fault Tolerance**: Robust system design to ensure minimal downtime and data integrity.
- **Seamless Integration**: Supports smooth music streaming and user interaction.

## Architecture Overview
The architecture consists of:
1. **Django Server**: Manages the core backend logic.
2. **Kafka**: Facilitates real-time data pipelines.
3. **Cassandra**: Stores user interaction data for scalability.
4. **CockroachDB**: Stores structured metadata for efficiency.
5. **AWS S3 Bucket & CloudFront**: Handles music file storage and delivery.
6. **Client**: Connects to the server for user interaction and streaming.

![Architecture Diagram](https://drive.google.com/uc?id=1qv3ICie8Zwed2Mzp3-gylXNbCkmceVzJ)

## Setup Instructions

### Installation
#### Setup for Cassandra
1. Adding Cassandra image:-
   ```bash
   docker pull Cassandra
   ```

2. Listing all the docker images (Cassandra should appear):-
   ```bash
   docker image list
   ```

3. Starting Cassandra node 1 :-
- Change the path according to your convenience.
   ```bash
    docker run --name audio_node1 -p 9042:9042 -v "{path}:/var/lib/cassandra/data" -e CASSANDRA_CLUSTER_NAME=AudioCluster -e CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch -e CASSANDRA_DC=datacenter1 -d Cassandra
   ```
4. Checking the status of node 1 (Make sure that it appears like this
    ```bash
	docker exec -it audio_node1 nodetool status
    ```
5. After making sure that status is correct then start 2nd node:
- Change the path here also accordingly
   ```bash
   docker run --name audio_node2 -v "{path}:/var/lib/cassandra/data" -e CASSANDRA_SEEDS="$(docker inspect --format='{{ .NetworkSettings.IPAddress }}' audio_node1)" -e CASSANDRA_CLUSTER_NAME=AudioCluster -e CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch -e CASSANDRA_DC=datacenter1 -d cassandra:latest
   ```

6. Open the CQL shell:
   ```bash
   docker exec -it cas2  cqlsh
   ```

7. Create a keyspace (like database in SQL):
   ```bash
   CREATE KEYSPACE audio_streaming_keyspace WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor' : 2};
   ```

8. To use the keyspace:
   ```bash
   USE audio_streaming_keyspace;
   ```

That's it for the initial setup for Cassandra in docker. Always keep docker running and also don't forget to restart nodes if you close docker.

#### Setup for kafka
1. Install Kafka and make sure it is located in the root directory. 

2. From the Kafka folder (stored in the root directory), open up three terminals and run zookeeper, server and create Kafka Topics with the commands given below in the three separate terminals.

Zookeeper and Server (Windows):
   ```bash
   .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
   .\bin\windows\zookeeper-server-start.bat .\config\server.properties
   ```

Topics (Windows):
   ```bash
   .\bin\windows\kafka-topics.bat --create --topic listening_history --bootstrap-server localhost:9092
   .\bin\windows\kafka-topics.bat --create --topic playlist_create --bootstrap-server localhost:9092
   .\bin\windows\kafka-topics.bat --create --topic playlist_delete --bootstrap-server localhost:9092
   .\bin\windows\kafka-topics.bat --create --topic playlist_add_song --bootstrap-server localhost:9092
   .\bin\windows\kafka-topics.bat --create --topic playlist_remove_song --bootstrap- server localhost:9092
   ```

Note: Ensure that zookeeper and server are running correctly in the background when starting the application. Kafka topics need to be created only once.

#### To start the application:
1. Navigate to the folder.
2. Open up two terminals.
2. In the first terminal, run the following command for starting the Kafka consumer.
    ```bash
	python .\music\kafka_consumer.py
    ```
3. In the second terminal, for starting the Django application.
    ```bash
    pip install -r requirements.txt
	python .\manage.py runserver
    ```
4. In a browser, open the url of the locahost listed. http://localhost:8000/login.

Here is the required data to upload a song.

##### Artist ID: 1024921636833263617
##### Album ID: 1024921637392220161
