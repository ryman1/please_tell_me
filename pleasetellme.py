#!/usr/bin/python

import tweepy
import json
import re

def wordreplace(sentance, mapfile):
    sentencelist = sentance.split()
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
    mappingdict = {}
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
                    for index in indexestoreplace:
                        allowedtoreplace = True
                        # If this word has already been replaced before
                        if wordreplaced[index]:
                            allowedtoreplace = False
                            # print('word at index ' + index + ' has already been replaced')
                            break
                    if allowedtoreplace:
                        # print 'we are allowed to replace'
                        wordreplaced[index] = True
                        replacements = zip(indexestoreplace, mappingdict[key].split())
                        for replacement in replacements:
                            sentencelist[replacement[0]] = replacement[1]
                    # else:
                        # print('Some or all of these words have already been replaced')
                # print('Phrase to find: ' + phrasetofind)
                # print('Checking against ' + wordsbeingchecked)
                wordsbeingchecked = ''
    finalsentance = ''
    for word in sentencelist:
        finalsentance += word + ' '
    return finalsentance.rstrip().capitalize()
            # searchpattern = re.compile(phrasetofind, re.IGNORECASE)
            # if searchpattern.search(sentance):
            #     # Check whether the match is a word that was already replaced
            #     for wordnumber in range(0,len(sentance.split())):
            #         for word in phrasetofind.split():
            #
            #     newsentance = re.sub(' ' + phrasetofind + ' ', ' ' + mappingdict[key] + ' ', sentance)
            # # Mark any words that have changed, so we don't replace them again
            # for wordnumber in range(0, len(newsentance.split())):
            #     if newsentance[wordnumber] != sentance[wordnumber]:
            #         wordreplaced[wordnumber] = True

if __name__ == '__main__':
    with open('config.json') as configfile:
        config = json.load(configfile)
    auth = tweepy.OAuthHandler(config['CONSUMER_KEY'], config['CONSUMER_SECRET'])
    auth.set_access_token(config['ACCESS_KEY'], config['ACCESS_SECRET'])
    api = tweepy.API(auth)

    for tweet in tweepy.Cursor(api.search,
                               q="please tell me",
                               rpp=100,
                               result_type="recent",
                               include_entities=True,
                               lang="en").items(200):
        try:
            searchresult = re.search(r'^[pP]lease tell me', tweet.text)
            if searchresult:
                print('Tweet: ' + tweet.text)
                newtweet = re.sub('[pP]lease tell me', '', tweet.text)
                print('Tweet Reply: ' + wordreplace(newtweet, 'wordsubstitutions') + '\n')
        except UnicodeEncodeError:
            pass
    pass