import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """Processes song file.
    
    Artist information is inserted into the 'artists' table. And Song information
    is inserted into the 'songs' table.
    
    Args:
        cur (psycopg2.cursor): A database cursor
        filepath (str): A filepath to a song file
    these are essential for creating and accessing database
    """
    # open song file
    df = pd.read_json(filepath, lines=True)
    # insert song record
    song_data = df[['song_id', 'title', 'artist_id', 'year', 'duration']].values[0].tolist()
    cur.execute(song_table_insert, song_data)
    # insert artist record
    artist_data = df[['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude']].values[0].tolist()
    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    """Processes log file.
    
   Time information is inserted into the 'time' table. User information
    is upserted into the 'users' table. And Songplay information is
    inserted into the 'songplays' table.
    
    Args:
        cur (psycopg2.cursor): A database cursor
        filepath (str): A filepath to a log file
    these are essential for creating and accessing database
    """
    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df[df.page == 'NextSong'] 

    # convert timestamp column to datetime
    t = df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    t = df.copy()
    
    # insert time data records
    time_data = (t.ts, t.ts.dt.hour , t.ts.dt.day , t.ts.dt.dayofweek , t.ts.dt.month , t.ts.dt.year , t.ts.dt.weekday)
    column_labels = ['start_time', 'hour', 'day', 'week', 'month', 'year', 'weekday']
    stick = dict(zip(column_labels, time_data))
    # insert time data records
    time = pd.DataFrame(stick) 
    
    for i, row in time.iterrows():
        cur.execute(time_table_insert, list(row))
    
    
    # load user table
    user_df = df[["userId", "firstName", "lastName", "gender", "level"]]
    

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)
    df['ts'] = pd.to_datetime(df["ts"], unit='ms')
    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = [row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent]
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    """
    this function is used for process Jason file using data directory path it's used to process both files log/songs
     Args:
        cur (psycopg2.cursor): A database cursor
        conn (psycopg2.connection): A database connection
        filepath (str): A filepath of the directory to process
        func (function): The function to call for each found file
    """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    """
    the main script code 
    used to :
        create database and establish connection
        process data from files directories
    close database connection 
    """
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()