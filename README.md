# SteemSTEM-reputation

A good reputation system for SteemSTEM community must in my opinion include two
ingredients, an authorship component and an engagement component, contributing
in equal parts.

## AUTHORSHIP INDICATOR

The authorship metric is built from a few key principles.

Each SteemSTEM vote on a post at x% gives x reputation points at the time of the
vote. The value of the reputation points vary with time. An exponential decay is
used, the authorship point half-life being a free parameter. As SteemSTEM
strives to push for quality as much as possible, a small number of good posts is
favored upon a larger number of moderately good posts. We divide the score by
the square root of the number of posts.

Finally, we can remove individuals from the algorithm and, the total amount of
reputation points is fixed to a given value.

## ENGAGEMENT INDICATOR

Here, I track every single comment to any SteemSTEM-supported post and give
reputation points to the comment author.

First, if the comment length is smaller than N characters, no point is given
(spam). Moreover, if the comment has been posted more than W weeks after the
SteemSTEM vote, no point is given. I want meaningful comments that help
illustrating that supported posts are interesting during the time in which
they are hot or trending on the #Steemstem tag.

If non zero, the score is given by the square root of the comment length. As
with the authorship indicator, any earned engagement point loses value with
time, the score today is divided by the square root of the number of comments
and some individuals can be removed from the algorithm.

The final score is normalized as for the authorship case, the total number of
available points being the same as for the authorship indicator.

## FINAL REPUTATION INDICATOR

The final reputation is given by the average of the two above metrics.

## MORE ABOUT THE CODE

The code can be obtained from
  https://github.com/BFuks/SteemSTEM-reputation
and requires steem-python (https://github.com/Steemit/Steem-python).

To run it, it is sufficient to complete the setup part of the code,
```
## Setup
 half_life_vote    = 3.5*30*24*3600.     # 3.5 months - authorship point half-life
 half_life_comment = 1.75*30*24*3600.    # 1.75 month - engagement point half-life
 comment_timelimit = 14*24*3600.         # 2 weeks - the W number
 comment_spam_limit= 100                 # minimum number of characters for a comment to be valid (N)
 comment_filename  = 'comments_data.txt' # where to save the treated comments
 load_backup = True                      # Using the file with the saved comments
 normalized_rep = 1000                   # Score normalization

## Exclusions
 team = [ ‘null’ ]
 bots = [ ]
 blacklist = [ ]
```
and execute the program.
