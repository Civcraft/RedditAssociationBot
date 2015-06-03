# To be used with the minecraft plugin found at https://github.com/Civcraft/RedditAssociation
#
# Thanks to this https://github.com/Civcraft/modmail_ticketmanager I managed to have some idea
# of that I was doing.
#
# This bot is used to communicate with minecraft names and confirm that the player
# is who they say they are.
#
# Dendencies:
# python, mysql, praw

debug = False

redditUsername = ''
redditPassword = ''

# The time between checks that the bot makes to call the database and check if any new 
# names need to be sent a message.
reddit_Minutes_Between_Messages = 1

# The mysql information should be entered here.  Make sure it is the same as the information
# in the plugin.  Make sure the plugin gets loaded first as it will generated all the necessary
# tables.
mysql_username = ''
mysql_password = ''
mysql_host = 'localhost'
mysql_dbname = 'bukkit'

prawUserAgent = 'RedditAssociationBot v1.0 by /u/rourke750'

# The subject of the message line.
reddit_message_subject = 'AUTHENTICATING MINECRAFT USERNAME'
# If it should be sent as the subreddit, leave as is to send as the user.
subreddit = 'None'

import mysql.connector
import sys
import praw
import time
import random

global cnx
global r

# Mysql Statements
find_poll = ("select * from RedditBotLookUp")
remove_user_from_poll = ("delete from RedditBotLookUp where uuid = %s")
add_user_to_redditcode = ("insert into RedditCode(code, uuid, reddit_name) values(%s, %s, %s)")

def log(message):
    sys.stdout.terminal.write(message)

def check_mysql_connection():
    try: 
        cnx = mysql.connector.connect(user=mysql_username, password=mysql_password,
                              host=mysql_host,
                              database=mysql_dbname)
        return True
    except mysql.connector.Error as err:
        log(message="Mysql connection could not be established.")
        return False
        
def log_into_reddit():
    r = praw.Reddit(user_agent=prawUserAgent)
    r.login(redditUsername, redditPassword)

def main_loop():
    poll_users()
    
# This method is used to send messages to reddit users in order to get them to confirm
def poll_users():
    cursor = cnx.cursor()
    cursor.execute(find_poll)
    for (name, uuid, reddit_name) in cursor:
        message = 'The minecraft account ' + name + ' has stated that this account should be associated. '
        rand = random.randint(0, 10000000)
        message += 'Type the command /arc ' + rand + " in game to associate this account."
        r.send_message(reddit_name, reddit_message_subject, message, from_sr=subreddit, captcha=None)
        curs = cnx.cursor()
        curs.execute(remove_user_from_poll, uuid)
        cnx.commit()
        curs.execute(add_user_to_redditcode, (rand, uuid, reddit_name))
        cnx.commit()
    
if __name__ == '__main__':
    if not check_mysql_connection():
        exit
    log_into_reddit()
    while True:
        main_loop()
        time.sleep(reddit_Minutes_Between_Messages* 60)