# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-04-18

### Added
- Socket timeout mechanism for RSS feed parsing (default: 10 seconds)
- Automatic encoding detection and correction for article content extraction
- Intelligent encoding fallback using `apparent_encoding` when `ISO-8859-1` is detected

### Fixed
- **Critical**: Character encoding issues causing garbled Chinese text in RSS feeds
  - Fixed People's Daily RSS feed displaying corrupted characters
  - Fixed iDaily and other feeds with mixed Chinese/English content
- RSS feed parsing hanging indefinitely on slow/unresponsive servers
  - huxiu.com feed now times out after 10 seconds instead of 60+ seconds
- Optimized log levels: `CharacterEncodingOverride` warnings downgraded to DEBUG
- Simplified article ID strategy to use only `published` timestamp for consistency

### Changed
- Feed timeout behavior: RSS feed timeouts now log warnings only (no blacklist)
- Article extraction timeout behavior: Article content timeouts still add domains to blacklist
- Improved error messages for timeout and encoding issues

### Technical Details
- **Encoding Fix**: Modified `ArticleExtractor._get_html()` to detect and correct `ISO-8859-1` encoding
- **Timeout Fix**: Added `socket.setdefaulttimeout()` in `FeedParser._fetch_feed_with_retry()`
- **Log Optimization**: Separated encoding warnings from actual parsing errors

### Test Coverage
- Verified encoding fix with:
  - People's Daily RSS (`plink.anyfeeder.com/people-daily`)
  - iDaily RSS (`plink.anyfeeder.com/idaily/today`)
  - William Long RSS (`www.williamlong.info/rss.xml`)
- All unit tests passing (48/48 core modules)

## [1.1.2] - 2026-04-15

### Fixed
- Version number consistency across project files

## [1.1.1] - 2026-04-14

### Added
- ID-based deduplication strategy with priority ordering

### Fixed
- Sogou WeChat search URL extraction and permanent blacklist

## [1.1.0] - 2026-02-09

### Initial Release
- RSS/Atom feed parsing from Feedland OPML
- Multi-strategy article content extraction
- Domain blacklist management
- Parallel feed processing
- Configurable retention policies
