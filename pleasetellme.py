#!/usr/bin/python

import tweepy
import json
import re
import collections
import time


def wordreplace(sentence, mapfile):
    sentencelist = sentence.split()
    with open(mapfile) as f:
        maplist = f.readlines()
    # dict that tracks if a word has already been replaced
    wordreplaced = {}
    for wordnumber in range(0, len(sentencelist)):
        wordreplaced[wordnumber] = False
    # # List that has all sentance words and whether it has already been replaced
    # for word in sentance.split():
    #     sentancewords.append([word, False])
    # Create a dict of all the word replacements
    mappingdict = collections.OrderedDict()
    for line in maplist:
        wordkeys = line.split(':')[0].split(',')
        wordkeys = tuple([item.lower() for item in wordkeys])
        replacevalue = line.split(':')[1]
        mappingdict[wordkeys] = replacevalue
    # Go through words/phrases to see if any of them are in the sentance
    for key in mappingdict.iterkeys():
        for phrasetofind in key:
            # Find how many words we want to replace (x) depending on how many words are in the phrase to find
            numofwords = len(phrasetofind.split())
            # Go through the sentence looking at x number of words at a time.
            wordsbeingchecked = ''
            for wordnumber in range(0, len(sentencelist)-numofwords):
                for num in range(wordnumber, wordnumber+numofwords):
                    if wordsbeingchecked:
                        wordsbeingchecked += ' ' + sentencelist[num]
                    else:
                        wordsbeingchecked = sentencelist[num]
                if re.search(r'^' + phrasetofind.lower() + r'(?=[\.])*$', wordsbeingchecked.lower()):
                    # print 'found match of ' + phrasetofind + ' at position/s '
                    indexestoreplace = []
                    # Store the index of the words we want to replace
                    for num in range(wordnumber, wordnumber+numofwords):
                        # print num
                        indexestoreplace.append(num)
                    allowedtoreplace = True
                    for index in indexestoreplace:
                        # If this word has already been replaced before
                        if wordreplaced[index]:
                            allowedtoreplace = False
                            # print('word at index ' + index + ' has already been replaced')
                            break
                    if allowedtoreplace:
                        # print 'we are allowed to replace'
                        for i in indexestoreplace:
                            wordreplaced[i] = True
                        # if len(indexestoreplace) == len(mappingdict):
                            replacements = zip(indexestoreplace, mappingdict[key].split())
                        # If we're replace multpile words with fewer words
                        if len(indexestoreplace) > len(mappingdict[key].split()):
                            lengthdiff = len(indexestoreplace) - len(mappingdict[key].split())
                            for wordnumbertoremove in range(indexestoreplace[0]+1, lengthdiff+1):
                                sentencelist.pop(wordnumbertoremove)
                                del wordreplaced[wordnumbertoremove]
                                print wordnumbertoremove
                        for replacement in replacements:
                            sentencelist[replacement[0]] = replacement[1]
                wordsbeingchecked = ''
    sentencelist[0] = sentencelist[0].capitalize()
    finalsentence = ''
    for word in sentencelist:
        finalsentence += word + ' '
    return finalsentence.rstrip().replace('?', '.')


def sendtweet(message, to, inreplyto=None):
    api.update_status(status='@' + to + ' ' + message, in_reply_to_status_id=inreplyto)

if __name__ == '__main__':
    with open('config.json') as configfile:
        config = json.load(configfile)
    auth = tweepy.OAuthHandler(config['CONSUMER_KEY'], config['CONSUMER_SECRET'])
    auth.set_access_token(config['ACCESS_KEY'], config['ACCESS_SECRET'])
    api = tweepy.API(auth)
    with open('greatestid') as g:
        greatestid = g.readline()
        tempgreatestid = int(greatestid)
    tweetssent = 0
    while True:
        for tweet in tweepy.Cursor(api.search,
                                   q="please tell me that",
                                   rpp=300,
                                   result_type="recent",
                                   include_entities=True,
                                   lang="en",
                                   since_id=int(greatestid)
                                   ).items(500):
            try:
                searchresult = re.search(r'^[pP]lease tell me (?!(who|what|where|when|how|why|that(?!\'s)|more|about))', tweet.text)
                if searchresult:
                    print('Tweet: ' + tweet.text)
                    # Remove Please tell me
                    newtweet = re.sub('([pP]lease)? tell me', '', tweet.text)
                    # remove periods from mr mrs and dr
                    newtweet = re.sub(r'([mMdDsS][rR][s]?)\.', r'\1', newtweet)
                    # Use only the first sentence
                    try:
                        newtweet = re.search(r'(^.*?(!|\.|\?)+)', newtweet).group(0)
                    except AttributeError:
                        pass
                    # remove urls
                    newtweet = re.sub(r'http.*?( |$)', '', newtweet)
                    if len(newtweet) <= int(config['tweet_length_limit']):
                        # substitute words
                        newtweet = wordreplace(newtweet, 'wordsubstitutions')
                        print('Tweet Reply: ' + newtweet + '\n')
                        print('sent: ' + str(tweet.created_at))
                        sendtweet(newtweet, tweet.user.screen_name, tweet.id)
                        print('Tweet sent\n')
                        tweetssent += 1
                        if tweet.id > tempgreatestid:
                            tempgreatestid = tweet.id
                    else:
                        continue
            except UnicodeEncodeError:
                pass
            if tweetssent >= int(config['tweets_to_send_per_run']):
                break
        if not greatestid:
            greatestid = '0'
        # Update the greatest id that we've tweeted to, so we don't reply to old stuff.
        if tempgreatestid > long(greatestid):
            with open('greatestid', 'w') as gid:
                gid.write(str(tempgreatestid))
        print('sleeping for ' + config['seconds_sleep_between_runs'] + ' seconds.')
        time.sleep(int(config['seconds_sleep_between_runs']))
