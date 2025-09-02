#!/bin/sh
# The Ultimate AttentionSync - One Line
curl -s "${1:-https://news.ycombinator.com/rss}" | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | head -10