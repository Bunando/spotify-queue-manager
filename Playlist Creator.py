import streamlit as st
import spotipy
from spotipy import SpotifyOAuth
import csv
import random

client_id = "a3bb7b8990ed44dbab8a7f08f2eb35c9"
client_secret = "c462fd98ef4d4d9494c74a104b65c0d2"
scope = ["user-library-read", "playlist-read-private", "playlist-modify-private", "user-modify-playback-state"]

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                            client_secret=client_secret,
                                            redirect_uri="http://localhost:1234",
                                            scope=scope),
                    retries=0)

allLikedSongs = []
likedSongs = []
nonLikedSongs = []

def main():
    global allLikedSongs
    global likedSongs
    global nonLikedSongs
    
    with open('Liked Songs.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            likedSongs.extend(row)

    with open('Non-Liked Songs.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            nonLikedSongs.extend(row)

    with st.form("my_form"):
        number = st.number_input("Add _ of Songs: ", step=1)
        st.form_submit_button()
    
    # Fill up nonLikedSongs to prevent while loop from exiting immediately
    if nonLikedSongs == []:
        refreshNonLikedSongs()

    st.write("Creating Song List...")
    addedSongs = []
    for _ in range(0, (number+1)//2):
    # while nonLikedSongs != []:
        if likedSongs == []:
            refreshLikedSongs()
        if nonLikedSongs == []:
            refreshNonLikedSongs()
        
        addedSongs.append(likedSongs.pop())
        addedSongs.append(nonLikedSongs.pop())

    addSongsToQueue(addedSongs)
    # addSongsToPlaylist(addedSongs, "spotify:playlist:0MIAT2tj0oFEdf3idIRETE")

    with open('Liked Songs.csv', 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the data rows
        csvwriter.writerow(likedSongs)

    with open('Non-Liked Songs.csv', 'w') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)
        # writing the data rows
        csvwriter.writerow(nonLikedSongs)

def refreshLikedSongs():
    global allLikedSongs
    global likedSongs
    likedSongs = (allLikedSongs if allLikedSongs != [] else getLikedSongs())
    random.shuffle(likedSongs)
    # Store all liked songs for future use
    allLikedSongs = likedSongs.copy()

def refreshNonLikedSongs():
    global allLikedSongs
    global nonLikedSongs
    st.write("Getting All Songs...")
    playlistSongs = getPlaylistSongs("spotify:playlist:7Lp7Bv2OtPB0N4DRRPzrG3")
    if allLikedSongs == []:
        allLikedSongs = getLikedSongs()
    nonLikedSongs = [song for song in playlistSongs if song not in allLikedSongs]
    st.write(len(nonLikedSongs))

    # Add potential songs to list
    st.write("Getting Additional Songs...")
    nonLikedSongs.extend(getPlaylistSongs("spotify:playlist:6IfgDbYGXMuLIC78uW4G8t"))

    random.shuffle(nonLikedSongs)

def getLikedSongs(): 
    st.write("Getting Liked Songs...")
    likedSongs = []
    newResult = sp.current_user_saved_tracks(limit=50)

    while newResult != None:
        for song in newResult['items']:
            if not song['track']['is_local']:
                likedSongs.append(song['track']['uri'])
        newResult = sp.next(newResult)
    return likedSongs


def getPlaylistSongs(playlist_id: str): 
    playlistSongs = []
    newResult = sp.playlist_tracks(playlist_id=playlist_id)

    while newResult != None:
        for song in newResult['items']:
            if not song['is_local']:
                playlistSongs.append(song['track']['uri'])
        newResult = sp.next(newResult)

    return playlistSongs

def addSongsToQueue(songList: list):
    st.write("Queuing All Songs...")
    for song in songList:
        sp.add_to_queue(uri=song)

def addSongsToPlaylist(songList: list, playlist_id: str):
    st.write("Adding All Songs...")
    offset = 0
    subsection = songList[100*offset:100*(offset+1)]
    while subsection != []:
        sp.playlist_add_items(playlist_id, subsection)
        offset += 1
        subsection = songList[100*offset:100*(offset+1)]


if __name__ == "__main__":
    main()