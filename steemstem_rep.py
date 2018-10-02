#!/usr/bin/env python

# imports
import math
import os
import time
from datetime import datetime, timedelta
from operator import itemgetter
from steem import Steem, post

# setup
half_life_vote = 3.5 * 30 * 24 * 3600.  # 3.5 months - authorship point half-life
half_life_comment = 1.75 * 30 * 24 * 3600.  # 1.75 month - engagement point half-life
comment_timelimit = 14 * 24 * 3600.  # 2 weeks - the W number
comment_spam_limit = 100  # minimum number of characters for a comment to be valid (N)
comment_filename = 'comments_data.txt'  # where to save the treated comments
load_backup = True  # Using the file with the saved comments
normalized_rep = 1000  # Score normalization

## general
normalized_rep = 1000.
team = ['null']
bots = []
blacklist = []

# Welcome message
print("Start of the run on:", time.asctime(time.localtime(time.time())), '\n')

# Get all steemstem votes
s = Steem()
all_votes = s.get_account_votes("steemstem")


# Method to get each post reputation value, and adding it to the associated author
def get_scores(excluded=[]):
    author_scores = {}
    comment_scores = {}
    comment_backup = {}

    # saving a comment score
    def save(dico, author, val):
        if not author in excluded:
            if not author in dico.keys():
                dico[author] = [val, 1]
            else:
                dico[author] = [dico[author][0] + val, dico[author][1] + 1]

    ## Loading the comments from the backup file (if activated)
    if load_backup:
        if os.path.isfile(os.path.join(os.getcwd(), comment_filename)):
            comment_file = open(os.path.join(os.getcwd(), comment_filename), 'r')
            for line in comment_file:
                if 'null' in line:
                    V_comment = 0
                else:
                    d_time = float(line.split()[5])
                    cd_time = (datetime.now() - datetime.strptime(line.split()[3] + 'T' + line.split()[4],
                                                                  "%Y-%m-%dT%H:%M:%S")).total_seconds()
                    c_len = float(line.split()[2])
                    if c_len > comment_spam_limit and (d_time - cd_time) < comment_timelimit:
                        V_comment = math.sqrt(c_len) * math.exp(-math.log(2.) * cd_time / half_life_comment)
                    else:
                        V_comment = 0
                if line.split()[0] not in comment_backup.keys():
                    comment_backup[line.split()[0]] = [[line.split()[1], V_comment]]
                else:
                    comment_backup[line.split()[0]].append([line.split()[1], V_comment])
            comment_file.close()

    for single_vote in all_votes:
        ## checking if not a voted comment
        if single_vote['authorperm'].split('/')[1].startswith('re-'):
            continue

        ## we have a voted post: we move on and calculate the post score
        delta_time = (datetime.now() - datetime.strptime(single_vote['time'], "%Y-%m-%dT%H:%M:%S")).total_seconds()
        V_post = single_vote['percent'] / 10000. * math.exp(-math.log(2.) * delta_time / half_life_vote)

        ## Now the comments. First, we try to get the info from the comment backup file
        if single_vote['authorperm'] in comment_backup.keys():
            for auth, val in comment_backup[single_vote['authorperm']]:
                save(comment_scores, auth, val)
        ## If not in the backup file, we read from the blockchain
        else:
            print(" New posts = ", single_vote['authorperm'])
            ## just to leave a trace, important for non commented posts (irrelevant for the other posts)
            comment_file = open(os.path.join(os.getcwd(), comment_filename), 'a')
            if delta_time > comment_timelimit:
                print("    *** adding tag in the comment file")
                comment_file.write(single_vote['authorperm'] + ' null 0 0 0 0\n')
            comment_file.close()
            ## now the main meat
            all_comments = post.Post.get_replies(post.Post('@' + single_vote['authorperm']))
            for single_comment in all_comments:
                comment_delta_time = (datetime.now() - single_comment['created']).total_seconds()
                if len(single_comment['body']) > comment_spam_limit and (
                        delta_time - comment_delta_time) < comment_timelimit:
                    V_comment = math.sqrt(len(single_comment['body'])) * math.exp(
                        -math.log(2.) * comment_delta_time / half_life_comment)
                else:
                    V_comment = 0.
                save(comment_scores, single_comment['author'], V_comment)
                ## If the steemstem vote is older than 2 weeks old, we store in the backup file as no more comment points
                if delta_time > comment_timelimit:
                    print("    *** added to the comment file")
                    comment_file = open(os.path.join(os.getcwd(), comment_filename), 'a')
                    comment_file.write(single_vote['authorperm'] + ' ' + single_comment['author'] + ' ' + \
                                       str(len(single_comment['body'])) + ' ' + str(single_comment['created']) + ' ' + \
                                       str(delta_time) + '\n')
                    comment_file.close()

        ## Back to the post: storing the post score
        save(author_scores, single_vote['authorperm'].split('/')[0], V_post)

    # Normalizing the post and comment scores relatively to the number of posts
    for x in author_scores.keys():
        author_scores[x] = author_scores[x][0] / math.sqrt(author_scores[x][1])
    for x in comment_scores.keys():
        comment_scores[x] = comment_scores[x][0] / math.sqrt(comment_scores[x][1])

    # output
    return [author_scores, comment_scores]


# Get normalized author reputation indicators + ordering
def normalize(dico, total):
    total_rep = sum([float(x[1]) for x in dico])
    new_dico = []
    for x in dico:
        new_dico.append([x[0], float(x[1]) / total_rep * total])
    return new_dico


[all_post_scores, all_comment_scores] = get_scores(excluded=team + bots + blacklist)

all_post_scores = list(reversed(sorted(all_post_scores.items(), key=itemgetter(1))))
all_comment_scores = list(reversed(sorted(all_comment_scores.items(), key=itemgetter(1))))
all_post_scores = normalize(all_post_scores, normalized_rep)
all_comment_scores = normalize(all_comment_scores, normalized_rep)

# Final reputation
all_authors = list(set([x[0] for x in all_post_scores] + [x[0] for x in all_comment_scores]))
all_rep_scores = []

for y in all_authors:
    rep = 0
    if y in [x[0] for x in all_post_scores]:
        rep += [x[1] for x in all_post_scores if x[0] == y][0]
    if y in [x[0] for x in all_comment_scores]:
        rep += [x[1] for x in all_comment_scores if x[0] == y][0]
    all_rep_scores.append([y, rep / 2.])
all_rep_scores = list(reversed(sorted(all_rep_scores, key=itemgetter(1))))

# print-out
print('Top authors [total: ' + str(len(all_post_scores)) + ']')
counter = 1
for x in all_post_scores:
    if x[1] > 1.0:
        print("{:3.0f}".format(counter), '{0: <20}'.format(x[0]), "{:10.3f}".format(x[1]))
        counter += 1
print('')

print('Top engaged members [total: ' + str(len(all_comment_scores)) + ']')
counter = 1
for x in all_comment_scores:
    if x[1] > 1.0:
        print("{:3.0f}".format(counter), '{0: <20}'.format(x[0]), "{:10.3f}".format(x[1]))
        counter += 1
print('')

counter = 1
for x in all_rep_scores:
    if x[1] > 1.0:
        print("{:3.0f}".format(counter), '{0: <20}'.format(x[0]), "{:10.3f}".format(x[1]))
        counter += 1

# Bye bye message
print("End of the run on:", time.asctime(time.localtime(time.time())), '\n')
