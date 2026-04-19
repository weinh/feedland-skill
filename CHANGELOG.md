# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.6] - 2026-04-19

### Fixed
- **Critical**: Fixed URL extraction for WeChat articles from Sogou search feeds
  - WeChat article URLs were incorrectly using Sogou search page links instead of original article URLs
  - Enhanced HTML entity decoding to handle double-encoded entities (&amp;amp; -> &)
  - All WeChat articles now correctly use mp.weixin.qq.com URLs with complete parameters

### Technical Details
- Updated `_extract_real_url_from_entry()` to use `html.unescape()` on HTML content before parsing
- Double HTML entity decoding: content unescape → link extraction → link unescape
- Verified with almosthuman2014 WeChat feed: all 5 articles now use correct WeChat URLs
- Fixes issue where results.json contained `weixin.sogou.com` links instead of `mp.weixin.qq.com`

## [1.2.5] - 2026-04-18

### Added
- HTML tag stripping for RSS description content when fallback is used
- Automatic HTML entity decoding (nbsp, lt, gt, amp, quot, mdash, hellip, etc.)

### Changed
- Content from description fallback is now cleaned of HTML tags before saving
- Preserves plain text content from extraction methods (Readability, Newspaper3k, etc.)

### Technical Details
- New `_strip_html_tags()` function in article_extractor module
- FeedParser checks `extraction_method` field: strips HTML only for "description-fallback"
- HTML entity decoding handles common RSS entities
- Text cleanup removes extra whitespace and blank lines after tag removal

### Test Coverage
- 14 new tests for HTML stripping functionality
- 3 integration tests for FeedParser HTML cleaning
- All tests passing (27/27)

## [1.2.4] - 2026-04-18

### Added
- Version number in startup log message for better tracking

### Changed
- Startup banner now includes version information to help identify which version is running

### Technical Details
- Added `logger.info(f"版本: {__version__}")` to startup sequence
- Helps users identify cache issues from old versions

## [1.2.3] - 2026-04-18

### Removed
- Unused blacklist management methods with no business value:
  - `clear_blacklist()` - Only used in tests
  - `cleanup_old_entries()` - No persistence, no cleanup needed
  - `remove_from_blacklist()` - Temporary blacklist, manual removal unnecessary
  - `to_dict()`/`from_dict()` - Persistence methods never used

### Changed
- **Code Simplification**: Removed 50+ lines of dead code from DomainBlacklist class
- **Test Cleanup**: Removed 7 obsolete test cases for deleted methods
- **Clearer Responsibilities**: DomainBlacklist now only handles core functionality (add, check, get)

### Technical Details
- Blacklist is runtime-only, resets on program restart
- No persistence to config file or disk
- Failed domains are tracked during execution but cleared on restart
- This design is intentional - network errors are often temporary

## [1.2.2] - 2026-04-18

### Fixed
- **Critical**: Logger configuration issue preventing module-specific logs from being written to files
  - Article extraction logs (network errors, extraction failures) were only shown in console
  - Now all module logs properly written to log files for post-analysis

### Added
- Feed name information in error logs for better issue tracking
  - "All extraction methods failed" now shows: URL - Feed Name
  - Network errors now show: URL - Feed Name - Error Details
  - Easier to identify which RSS source is causing problems

### Changed
- Logger configuration: now uses root logger to capture all module logs
  - `feedland_parser.article_extractor` logs now written to files
  - `feedland_parser.feed_parser` logs now written to files
  - All modules properly log to both console and file

### Technical Details
- **Root Logger**: Changed from named logger to root logger for comprehensive log capture
- **Feed Name Tracking**: Added `feed_name` parameter to extraction methods
- **Improved Error Context**: Error logs now include feed source identification
- **Better Debugging**: All critical errors now include URL + Feed Name for tracking

## [1.2.1] - 2026-04-18

### Fixed
- **Critical**: Sogou WeChat search articles being skipped when real URL extraction failed
  - Articles from `plink.anyfeeder.com/weixin/caozsay` and similar feeds now properly preserved
  - Content is extracted from RSS description even when original WeChat URL is not found
- Improved error logging to include URLs for better debugging
  - All extraction method failures now show the problematic URL
  - Network errors include both URL and error details
  - Article parsing errors show URL and title for identification

### Added
- `extraction_method` field to article output for tracking how content was extracted
- URL information to all critical error and warning log messages

### Changed
- Sogou WeChat search page handling: continue processing instead of skipping articles
- Log level for failed real URL extraction: WARNING → DEBUG

### Technical Details
- FeedParser no longer skips articles when real URL extraction fails
- ArticleExtractor now logs URLs in all error scenarios for better debugging
- Enhanced error tracking with URL and title information

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
