# -*- coding: utf-8 -*-
"""
Developed by : Apurva Kemkar

"""

import json
import datetime
import csv
import time
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

access_token = "EAACEdEose0cBANrDIRkGemOm6A31zQkK3a5WsWARKZC34XqLaqbvuZBc8spzB68iZAPfAMZAd4S2IMU8yW9KQ8BX6AAQIAzmbXpcXfeVse3swstfaRAXiCSDAmDETNFmYvMWE3MtrjykZBTxGQ3wAD8trUxH2RJIKN0vSoEOFXU5bCp0Fg9RW57ywg24ztwR1RRyLEsIzYwZDZD"

page_id = "LittleItalyVadodara"
file_id = "LittleItalyVadodara"
since_date = ""
until_date = ""

def request_until_succeed(url):
    req = Request(url)
    success = False
    while success is False:
        try:
            response = urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL {}: {}".format(url, datetime.datetime.now()))
            print("Retrying.")

    return response.read()

def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')

def processFacebookPageFeedStatus(status):
    status_published = datetime.datetime.strptime(status['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
    status_published = status_published + datetime.timedelta(hours=-5) # EST
    status_published = status_published.strftime('%Y-%m-%d %H:%M:%S') # best time format for spreadsheet programs

    status_id = status['id']
    likes_count = 0 if 'likes' not in status or status['likes'] is '' else status['likes']['summary']['total_count']
    shares_count = 0 if 'shares' not in status or status['shares'] is '' else status['shares']['count']
    return (status_id,status_published,likes_count,shares_count)

def processFacebookComment(comment,status_id):

    comment_published = datetime.datetime.strptime(
        comment['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    comment_published = comment_published + datetime.timedelta(hours=-5)  # EST
    comment_published = comment_published.strftime('%H:%M:%S')  # best time format for spreadsheet programs
    
    comment_message = '' if 'message' not in comment or comment['message'] \
        is '' else unicode_decode(comment['message'])

    comment_author = '' if 'from' not in comment or comment['from'] is '' else unicode_decode(comment['from']['name'])
    return (status_id,comment_published,comment_author)

def scrapeFacebookPageFeedStatus(page_id, access_token, since_date, until_date):
    with open('{}_facebook_statuses.csv'.format(page_id), 'w') as file:
        w = csv.writer(file)
        w.writerow(["status_id","status_created_time","likes_count","shares_count"])
        has_next_page = True
        num_processed = 0
        scrape_starttime = datetime.datetime.now()
        after = ''
        base = "https://graph.facebook.com/v2.9"
        node = "/{}/posts".format(page_id)
        parameters = "/?limit={}&access_token={}".format(100, access_token)
        since = "&since={}".format(since_date) if since_date \
            is not '' else ''
        until = "&until={}".format(until_date) if until_date \
            is not '' else ''

        print("Scraping {} Facebook Page: {}\n".format(page_id, scrape_starttime))

        while has_next_page:
            after = '' if after is '' else "&after={}".format(after)
            fields = "&fields=id,likes.summary(true),shares,created_time"
            url = base + node + parameters + after + since + until + fields
            #print(url)
            statuses = json.loads(request_until_succeed(url))
            
            for status in statuses['data']:
                status_data = processFacebookPageFeedStatus(status)
                #print(status_data)
                w.writerow(status_data)

                num_processed += 1
                if num_processed % 100 == 0:
                    print("{} Statuses Processed: {}".format
                          (num_processed, datetime.datetime.now()))

            # if there is no next page, we're done.
            if 'paging' in statuses:
                after = statuses['paging']['cursors']['after']
            else:
                has_next_page = False

        print("\nDone!\n{} Statuses Processed in {}".format(
              num_processed, datetime.datetime.now() - scrape_starttime))

def scrapeFacebookPageFeedComments(page_id, access_token):
    with open('{}_facebook_comments.csv'.format(file_id), 'w') as file:
        w = csv.writer(file)
        w.writerow(["Post_ID","Created_Time","Author"])

        num_processed = 0
        scrape_starttime = datetime.datetime.now()
        after = ''
        base = "https://graph.facebook.com/v2.9"
        parameters = "/?limit={}&access_token={}".format(
            5, access_token)

        print("Scraping {} Comments From Posts: {}\n".format(
            file_id, scrape_starttime))

        with open('{}_facebook_statuses.csv'.format(file_id), 'r') as csvfile:
            reader = csv.DictReader(csvfile)

            #Uncomment below line to scrape comments for a specific status_id
            #reader = [dict(status_id='5281959998_10151564774669999')]

            for status in reader:
                has_next_page = True

                while has_next_page:

                    node = "/{}/comments".format(status['status_id'])
                    after = '' if after is '' else "&after={}".format(after)
                    fields = "&fields=id,created_time,from"
                    url = base + node + parameters + after + fields
                    #print(url)
                    comments = json.loads(request_until_succeed(url))

                    for comment in comments['data']:
                        comment_data = processFacebookComment(comment, status['status_id'])
                        w.writerow(comment_data)
                        num_processed += 1
                        if num_processed % 100 == 0:
                            print("{} Comments Processed: {}".format(
                                num_processed, datetime.datetime.now()))

                    if 'paging' in comments:
                        if 'next' in comments['paging']:
                            after = comments['paging']['cursors']['after']
                        else:
                            has_next_page = False
                    else:
                        has_next_page = False

        print("\nDone!\n{} Comments Processed in {}".format(
            num_processed, datetime.datetime.now() - scrape_starttime))

if __name__ == '__main__':
    page_id = input("Enter Page name:")
    scrapeFacebookPageFeedStatus(page_id, access_token, since_date, until_date)
    scrapeFacebookPageFeedComments(file_id, access_token)

import csv
from functools import reduce
import operator
        
with open(r'{}_facebook_statuses.csv'.format(file_id), 'r') as f:
   reader = csv.reader(f,delimiter=',')
   my_list = list(reader)
    
with open(r'{}_facebook_comments.csv'.format(file_id), 'r') as f1:
   reader1 = csv.reader(f1,delimiter=',')
   my_list1 = list(reader1)

likes1 = 0
shares1 = 0
comment1=0

likes2 = 0
shares2 = 0
comment2=0

likes3 = 0
shares3 = 0
comment3=0

likes4 = 0
shares4 = 0
comment4=0

my_list = my_list[1:-1]
my_list1 = my_list1[1:-1]

for my in my_list1:
    time = int (my[1][0:2])
    if ((time>6) & (time<=12)):
        comment1 = comment1 + 1
        
    if ((time>12) & (time<=18)):
        comment2 = comment2 + 1
        
    if ((time>18) & (time<=24)):
        comment3 = comment3 + 1
        
    if ((time>0) & (time<=6)):
        comment4 = comment4 + 1
    
for my in my_list:
    time = int (my[1][11:13])
    #print(time)
    if ((time>6) & (time<=12)):
        
        likecount = int (my[2])
        sharecount= int (my[3])
        likes1 = likes1 + likecount
        shares1 = shares1 + sharecount
        
    if ((time>12) & (time<=18)):
        
        likecount = int (my[2])
        sharecount= int (my[3])
        likes2 = likes2 + likecount
        shares2 = shares2 + sharecount
        
    if ((time>18) & (time<=24)):
        likecount = int (my[2])
        sharecount= int (my[3])
        likes3 = likes3 + likecount
        shares3 = shares3 + sharecount
        
    if ((time>0) & (time<=6)):
        likecount = int (my[2])
        sharecount= int (my[3])
        likes4 = likes4 + likecount
        shares4 = shares4 + sharecount

print("Zone1 likes are: ", likes1 , " and shares are: ", shares1, "and comments are: ", comment1)
print("Zone2 likes are: ", likes2 , " and shares are: ", shares2, "and comments are: ", comment2)
print("Zone3 likes are: ", likes3 , " and shares are: ", shares3, "and comments are: ", comment3)
print("Zone4 likes are: ", likes4 , " and shares are: ", shares4, "and comments are: ", comment4)

from pylab import *

# make a square figure and axes
figure(1, figsize=(6,6))
ax = axes([0.1, 0.1, 0.8, 0.8])

# The slices will be ordered and plotted counter-clockwise.
labels = 'Morning(6am-12pm)', 'Afternoon(12pm-6pm)', 'Evening(6pm-12am)', 'Night(12am-6am)'
fracs = [likes1, likes2, likes3, likes4]
explode=(0.05, 0, 0, 0)

pie(fracs, explode=explode, labels=labels,
                autopct='%1.1f%%', shadow=True, startangle=90)
                # The default startangle is 0, which would start
                # the Frogs slice on the x-axis.  With startangle=90,
                # everything is rotated counter-clockwise by 90 degrees,
                # so the plotting starts on the positive y-axis.

title('LIKES', bbox={'facecolor':'0.8', 'pad':5})

show()

from pylab import *

# make a square figure and axes
figure(1, figsize=(6,6))
ax = axes([0.1, 0.1, 0.8, 0.8])

# The slices will be ordered and plotted counter-clockwise.
labels = 'Morning(6am-12pm)', 'Afternoon(12pm-6pm)', 'Evening(6pm-12am)', 'Night(12am-6am)'
fracs = [shares1, shares2, shares3, shares4]
explode=(0.05, 0, 0, 0)

pie(fracs, explode=explode, labels=labels,
                autopct='%1.1f%%', shadow=True, startangle=90)
                # The default startangle is 0, which would start
                # the Frogs slice on the x-axis.  With startangle=90,
                # everything is rotated counter-clockwise by 90 degrees,
                # so the plotting starts on the positive y-axis.

title('SHARES', bbox={'facecolor':'0.8', 'pad':5})

show()

from pylab import *

# make a square figure and axes
figure(1, figsize=(6,6))
ax = axes([0.1, 0.1, 0.8, 0.8])

# The slices will be ordered and plotted counter-clockwise.
labels = 'Morning(6am-12pm)', 'Afternoon(12pm-6pm)', 'Evening(6pm-12am)', 'Night(12am-6am)'
fracs = [comment1, comment2, comment3, comment4]
explode=(0.05, 0, 0, 0)

pie(fracs, explode=explode, labels=labels,
                autopct='%1.1f%%', shadow=True, startangle=90)
                # The default startangle is 0, which would start
                # the Frogs slice on the x-axis.  With startangle=90,
                # everything is rotated counter-clockwise by 90 degrees,
                # so the plotting starts on the positive y-axis.

title('COMMENTS', bbox={'facecolor':'0.8', 'pad':5})

show()
