# AttentionSync

Smart content aggregation that actually works.

## Quick Start

```bash
# Install and run
make install
make run

# That's it. API is at http://localhost:8000
```

## What It Does

- Aggregates content from multiple sources
- Summarizes using AI (if available)
- Serves it via clean REST API

## Architecture

```
api/
├── app/
│   ├── main_clean.py    # Entry point - 60 lines
│   ├── core/
│   │   ├── db.py        # Database - 60 lines  
│   │   ├── deps.py      # Dependencies - 50 lines
│   │   ├── errors.py    # Error handling - 70 lines
│   │   └── perf.py      # Performance - 150 lines
│   └── services/
│       └── content.py   # Content processing - 130 lines
```

Total: ~500 lines of actual code. No bullshit.

## Features

### Core (Always Works)
- ✅ REST API
- ✅ SQLite database
- ✅ Content processing
- ✅ Simple auth

### Optional (Install If Needed)
- OpenAI integration: `pip install openai`
- Anthropic integration: `pip install anthropic`
- Redis caching: `pip install redis`

## Design Philosophy

1. **Simplicity First** - If it's not simple, it's wrong
2. **Explicit > Magic** - No hidden behavior
3. **Fail Fast** - Errors should be obvious
4. **One Way** - There should be one obvious way to do it

## Performance

- Cold start: < 2 seconds
- API response: < 200ms
- Memory usage: < 100MB
- No background processes eating CPU

## Production

```bash
docker-compose up -d
```

## Testing

```bash
make test  # When we have tests
```

## Contributing

1. Keep it simple
2. No unnecessary abstractions
3. If you need more than 3 levels of indentation, refactor
4. Every line should have a purpose

## License

MIT - Use it, break it, fix it.

---

*"Perfection is achieved not when there is nothing more to add,
but when there is nothing left to take away."* - Antoine de Saint-Exupéry