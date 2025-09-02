# AttentionSync - Makefile Edition
# "Make is beautiful because it's declarative" - Linus would appreciate this

FEEDS = ~/.feeds
CACHE = ~/.attention
RSS = https://news.ycombinator.com/rss

# Default target
all: fetch show

# Add a feed
add:
	@echo "$(RSS)" >> $(FEEDS)
	@echo "Added: $(RSS)"

# Fetch all feeds
fetch:
	@mkdir -p $$(dirname $(CACHE))
	@touch $(FEEDS)
	@> $(CACHE)
	@while read url; do \
		curl -s "$$url" 2>/dev/null | \
		grep -o '<title>[^<]*</title>' | \
		sed 's/<[^>]*>//g' | \
		head -5 >> $(CACHE); \
	done < $(FEEDS)
	@echo "Fetched $$(wc -l < $(CACHE)) items"

# Show digest
show:
	@echo "=== Daily Digest ==="
	@cat $(CACHE) 2>/dev/null || echo "No items. Run: make fetch"

# Clean cache
clean:
	@rm -f $(CACHE)
	@echo "Cache cleaned"

# One-liner for everything
oneliner:
	@curl -s $(RSS) | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | head -10

# Help
help:
	@echo "AttentionSync - RSS in Make"
	@echo ""
	@echo "Usage:"
	@echo "  make add RSS=url  - Add feed"
	@echo "  make fetch        - Fetch all"  
	@echo "  make show         - Show digest"
	@echo "  make clean        - Clear cache"
	@echo "  make oneliner     - Direct fetch"
	@echo ""
	@echo "Example:"
	@echo "  make add RSS=https://example.com/rss"
	@echo "  make"

.PHONY: all add fetch show clean oneliner help