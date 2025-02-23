import streamlit as st
import spotipy
from spotipy import SpotifyOAuth
import csv
import random
import os

scope = ["user-library-read", "playlist-read-private", "playlist-modify-private", "user-modify-playback-state"]

oauth = SpotifyOAuth(client_id=st.secrets["CLIENT_ID"],
                    client_secret=st.secrets["CLIENT_SECRET"],
                    redirect_uri=st.secrets["REDIRECT_URI"],
                    scope=scope)

st.session_state["oauth"] = oauth

auth_url = oauth.get_authorize_url()

link_html = ' <a target="_self" href="{url}" >{msg}</a> '.format(
        url=auth_url,
        msg="Click me to authenticate!"
)

def sign_in():
    sp = spotipy.Spotify(auth=st.session_state["cached_token"])
    return sp

def get_token(oauth: SpotifyOAuth, code):
    token = oauth.get_access_token(code, as_dict=False, check_cache=False)
    os.remove(".cache")
    return token

if "cached_token" not in st.session_state:
    st.session_state["cached_token"] = ""

params = st.experimental_get_query_params()
sp = None
if st.session_state["cached_token"] != "":
    sp = sign_in()
# if no token, but code in url, get code, parse token, and sign in
elif "code" in params:
    # all params stored as lists, see doc for explanation
    st.session_state["code"] = params["code"][0]
    try: 
        token = get_token(st.session_state["oauth"], st.session_state["code"])
        st.session_state["cached_token"] = token
        sp = sign_in()
    except:
        st.write("Invalid token found for this session")
        st.markdown(' <a target="_self" href="/" >Click me to Refresh!</a> ', unsafe_allow_html=True)
# otherwise, prompt for redirect
else:
    st.write(" ".join(["No tokens found for this session. Please log in by",
                        "clicking the link below."]))
    st.markdown(link_html, unsafe_allow_html=True)
    st.markdown(f'[Or in a new tab!]({auth_url})')

allLikedSongs = []
likedSongs = []
nonLikedSongs = []

def main():
    global allLikedSongs
    global likedSongs
    global nonLikedSongs

    if not sp:
        return
    
    with open('Liked Songs.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            likedSongs.extend(row)

    with open('Non-Liked Songs.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            nonLikedSongs.extend(row)

    with st.form("my_form"):
        number = st.number_input("Number of Songs to Add: ", step=2)
        submitted = st.form_submit_button()

    if not submitted:
        return
    
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
    
    st.write("Done!")

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