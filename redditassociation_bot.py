# To be used with the minecraft plugin found at https://github.com/Civcraft/RedditAssociation
#
# Thanks to this https://github.com/Civcraft/modmail_ticketmanager I managed to have some idea
# of that I was doing.
#
# This bot is used to communicate with minecraft names and confirm that the player
# is who they say they are.
#
# Dendencies:
# python 2.7, mysql, praw

debug = False

redditUsername = ''
redditPassword = ''

# The time between checks that the bot makes to call the database and check if any new 
# names need to be sent a message.
reddit_Seconds_Between_Messages = 15

# The mysql information should be entered here.  Make sure it is the same as the information
# in the plugin.  Make sure the plugin gets loaded first as it will generated all the necessary
# tables.
mysql_username = ''
mysql_password = ''
mysql_host = 'localhost'
mysql_dbname = ''

prawUserAgent = 'CivcraftRedditAssociation v1.0 by /u/rourke750'

# The subject of the message line.
reddit_message_subject = 'AUTHENTICATING MINECRAFT USERNAME'
# The subreddit for the server, this should really be filled out.
subreddit = None
# If the bot should send as the subreddit.
should_send_as_subreddit = False
# If unregistered accounts should be able to post.
disable_unregistered_accounts = False
# The Subject of the message to send users when their post has been removed.
removed_subject_post = None
# The size at which at one point will clear the list of posts saved in ram.  It should be left at default.
max_threads_size = 1000

# -----------------------------------------------------------------------------------------------------------------------------

import mysql.connector
import praw
import sys, traceback
import time
import random
from datetime import datetime

cnx = None
r = None

# Mysql Statements
find_poll = ("select * from RedditBotLookUp")
remove_user_from_poll = ("delete from RedditBotLookUp where uuid = %(uuid)s")
add_user_to_redditcode = ("insert into RedditCode(code, uuid, reddit_name) values(%s, %s, %s)")
is_authenticated_user = ("select count(*) as count from redditrelations where reddit_name = %(reddit_name)s")

def log(message):
    print(message)

def check_mysql_connection():
    try:
        global cnx 
        cnx = mysql.connector.connect(user=mysql_username, password=mysql_password,
                              host=mysql_host,
                              database=mysql_dbname)
        return True
    except mysql.connector.Error as err:
        log('Mysql connection could not be established')
        return False
        
def log_into_reddit():
    global r
    r = praw.Reddit(user_agent=prawUserAgent)
    r.login(redditUsername, redditPassword)

def main_loop():
    log('Polling users to see if they are trying to register an account.')
    try:
        poll_users()
        if disable_unregistered_accounts:
            log('Checking to see if any users have posted that shouldn\'t be allowed to.')
            poll_subreddit()
    except:
        logException()
        
        
# This method is used to send messages to reddit users in order to get them to confirm
def poll_users():
    try:
        cursor = cnx.cursor()
        cursor.execute(find_poll)
        for name, uuid, reddit_name in cursor.fetchmany():
            message = 'The minecraft account ' + name + ' has stated that this account should be associated. '
            rand = ''.join((chr(random.randint(ord('a'),ord('z'))) for _ in xrange(16)))
            message += 'Type the command /arc ' + rand + " in game to associate this account."
            # Will send as the account unless specified otherwise
            sub = None
            if should_send_as_subreddit:
                sub = subreddit
            r.send_message(reddit_name, reddit_message_subject, message, from_sr=sub, captcha=None)
            curs = cnx.cursor()
            curs.execute(remove_user_from_poll, {'uuid': uuid})
            curs.execute(add_user_to_redditcode, (rand, uuid, reddit_name))
            cnx.commit()
            if debug:
                log(name + ' tried to register an account.')
            curs.close()
    finally:
        cnx.commit()
        cursor.close()

recent_posts = set()

def poll_subreddit():
    sub = r.get_subreddit(subreddit)
    for submission in sub.get_new():
        id = submission.id
        if id not in recent_posts:
            recent_posts.append(id)
            author = submission.author
            try:
                cursor = cnx.cursor()
                cursor.execute(is_authenticated_user, {'reddit_name': author})
                for count in cursor.fetch(limit=1):
                    if count == 0:
                        submission.delete()
                        message = 'Your message at ' + submission.short_link + ' has been removed do to you not being registered.\nTo register please log into your minecraft account and type \"/ar ' + author + '\" (without \"\").'
                        sub = None
                        if should_send_as_subreddit:
                            sub = subreddit
                        r.send_message(author, removed_subject_post, message, sub)
            finally:
                cnx.commit()
                cursor.close()
                
# This method will clear out recent_posts once it get too large
def handle_clear():
    size = len(recent_posts)
    if size > max_threads_size:
        recent_posts.clear()
                
def logException():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    msg = ['*** print_exc:', traceback.format_exc(), '*** tb_lineno: {0}'.format(exc_traceback.tb_lineno)]
    log.debug('\n'.join(msg))
    
if __name__ == '__main__':
    if not check_mysql_connection():
        sys.exit(0)
    log_into_reddit()
    while True:
        main_loop() 
        handle_clear()
        
        if debug:
            log("Pausing script.")
        time.sleep(reddit_Seconds_Between_Messages)
        if debug:
            log("Resuming script.")