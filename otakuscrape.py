#!/usr/bin/env python3

import argparse
import codecs
import os
import shlex
import subprocess
import sys
import urllib.parse as urlparse
import urllib.request as request

try:
	from bs4 import BeautifulSoup
except:
	print("OtakuSCRAPE: Import Error: OtakuSCRAPE depends on Beautiful Soup 4.", file=sys.stderr)
	print("Install with one of the following commands:", file=sys.stderr)
	print("  - pip3 install beautifulsoup4", file=sys.stderr)
	print("  - apt install python3-bs4", file=sys.stderr)
	sys.exit(1)

URI_TEMPLATE = None
USER_AGENT = None
OUTPUT_FILE_TEMPLATE = None
WGET = None
QUIET = False
SHELLCODE = False

PROVIDERS = ('www.rapidvideo.com', )

try:
	rc = subprocess.call(('wget', '--version'), stdout=open(os.devnull, 'wb'))
	WGET = 0 == rc
except Exception:
	WGET = False

def search_anime(anime):
	
	page = request.urlopen(request.Request('https://otakustream.tv/?s=' + urlparse.quote(anime, safe=''), headers={'User-Agent': USER_AGENT})).read()
	soup = BeautifulSoup(page, 'html.parser')

	results = soup.select('.animes-list > div > div > div > div > div > div > .ep-box')

	results = [r for r in results if r.select_one('.caption-category > .ep-no').string.strip() != 'Movie']

	if results:
		print('Search results for {}:'.format(anime))

		for result in results:
			print()
			print('Name:\t\t{}'.format(result.select_one('.caption-category > a').get_text()))
			aid = result.select_one('.cap-cat-hover > a')['href']
			aid = aid[7+aid.index('/anime/'):-1]
			print('Id:\t\t{}'.format(aid))
			print('Episodes:\t{}'.format(result.select_one('.caption-category > .ep-no').get_text().split()[-1]))
			print('Genres:\t\t{}'.format(', '.join([el.get_text() for el in result.select_one('.cch-content > p:nth-of-type(2)')('a')])))
			print('Premiered:\t{}'.format(', '.join([el.get_text() for el in result.select_one('.cch-content > p:nth-of-type(3)')('a')])))
	
	else:
		print('No results found for {}.'.format(anime))

def extract_strings(js):
	
	s = ''
	x = False
	for c in js:
		if c == '"':
			if x:
				yield s
			else:
				s = ''
			x = not x
		elif x:
			s += c

def get_quality(quality, qualities):
	
	if quality == 'HIGHEST':
		return max(qualities)
	
	if quality == 'LOWEST':
		return min(qualities)
	
	if isinstance(quality, str):
		quality = int(quality)
	
	if quality in qualities:
		return quality
	else:
		print("OtakuSCRAPE: Unavailable Quality: this video does not come in {}p quality".format(quality), file=sys.stderr)
		raise ValueError('Not in quality {}p'.format(quality))

def get_episode_uri(series, episode, quality):
	
	url = URI_TEMPLATE.format(series=series, episode=episode)
	try:
		resp = request.urlopen(request.Request(url, headers={'User-Agent': USER_AGENT}))
		if resp.geturl() != url:
			raise ValueError(url)
	
	except Exception as e:
		print("OtakuSCRAPE: Anime Not Found: No anime at {}".format(url), file=sys.stderr)
		raise e
	
	page = resp.read()
	soup = BeautifulSoup(page, 'html.parser')

	links = []
	
	for script in soup.find_all('script'):
		for string in extract_strings(script.get_text()):
			if string.startswith('/player.php'):
				links.append(codecs.encode(urlparse.parse_qs(urlparse.urlparse(string).query)['link'][0], 'rot13'))

	for prov in PROVIDERS:
		for l in links:
			if urlparse.urlparse(l).netloc == prov:
				provider = prov
				link = l
				break
		else:
			continue
		break
	else:
		print("OtakuSCRAPE: Unknown Provider: no known scraper for any available provider", file=sys.stderr)
		raise ValueError('No known providers')	

	if provider == 'www.rapidvideo.com':
		player_page = request.urlopen(request.Request(link, headers={'User-Agent': USER_AGENT})).read()
		player_soup = BeautifulSoup(player_page, 'html.parser')

		quality_buttons = player_soup.select('#home_video div > a')
		qualities = [int(el['href'][3+el['href'].index('&'):-1]) for el in quality_buttons]
		
		if qualities:
			video_quality = get_quality(quality, qualities)

			quality_player_page = request.urlopen(request.Request('{}&q={}p'.format(link, video_quality), headers={'User-Agent': USER_AGENT})).read()
			quality_player_soup = BeautifulSoup(quality_player_page, 'html.parser')

		elif quality in {'HIGHEST', 'LOWEST'}:
			quality_player_soup = player_soup

		else:
			get_quality(quality, (-1,))

		source = quality_player_soup.find('source')
		video_url = source['src']

		return video_url

	else:
		print("OtakuSCRAPE: Unknown Provider: no known scraper for provider {}".format(provider), file=sys.stderr)
		raise ValueError('Unknown provider {}'.format(provider))

def download_episode(series, episode, quality):
	
	outfile = OUTPUT_FILE_TEMPLATE.format(series=series, episode=episode)
	
	if not SHELLCODE:
		try:
			open(outfile, 'wb').close()
		except PermissionError as e:
			print("OtakuSCRAPE: Permission Error: unable to write to file '{}': Permission denied".format(outfile), file=sys.stderr)
			raise e

	if not QUIET: print('Looking up {} episode {}'.format(series, episode))

	try:
		uri = get_episode_uri(series, episode, quality)
	except Exception as e:
		if not QUIET: print('Failed to look up {} episode {}'.format(series, episode))
		os.unlink(outfile)
		raise e

	if not QUIET: print('Downloading {} episode {}'.format(series, episode))

	if SHELLCODE:
		print('wget -U {} -O {} {}'.format(shlex.quote(USER_AGENT), shlex.quote(outfile), shlex.quote(uri)))

	elif WGET:
		rc = subprocess.call(('wget', '-U', USER_AGENT, '-O', outfile, uri), stdout=(open(os.devnull, 'wb') if QUIET else sys.stdout))
		if rc != 0:
			print("OtakuSCRAPE: wget: return code was {}".format(rc), file=sys.stderr)
			if not QUIET: print('Failed to download {} episode {}'.format(series, episode))
			os.unlink(outfile)
			raise ValueError(str(rc))

		if not QUIET: print('Successfully downloaded {} episode {}'.format(series, episode))
	
	else:
		f = None

		try:
			f = open(outfile, 'wb')
			conn = request.urlopen(request.Request(uri, headers={'User-Agent': USER_AGENT}))

			written = 0

			data = conn.read(1 << 20)
			while data:
				f.write(data)
				written += len(data)
				if not QUIET: print('Downloaded {} bytes'.format(written), end='\r')
				data = conn.read(1 << 20)

			f.close()

			if not QUIET:
				print()
				print('Successfully downloaded {} episode {}'.format(series, episode))

		except Exception as e:
			if not QUIET:
				print()
				print('Failed to download {} episode {}'.format(series, episode))
			f.close()
			os.unlink(outfile)
			raise e


def download_episodes(series, episodes, quality):
	
	failures = 0

	for episode in episodes:
		try:
			download_episode(series, episode, quality)
		except Exception as e:
			print('An error occurred downloading episode {} of {}: {}: {}'.format(episode, series, type(e).__name__, e), file=sys.stderr)
			failures += 1
	
	if not QUIET:
		print('Downloaded {}/{} episodes.'.format(len(episodes) - failures, len(episodes)))
		print('{} episodes failed.'.format(failures))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='A tool for scraping anime off OtakuSTREAM')
	parser.add_argument('command', metavar='command', choices={'download', 'search'}, help="Valid commands are 'search' and 'download'")
	parser.add_argument('anime', help='If downloading, the anime to download. If searching, the search query.')
	parser.add_argument('episodes', type=int, nargs='*', help='The episodes to download')
	parser.add_argument('-r', '--quality', default='HIGHEST', dest='quality', help="The quality to download. Can be 'HIGHEST', 'LOWEST', or a number")
	parser.add_argument('-p', '--uri-pattern', default='https://otakustream.tv/anime/{series}/episode-{episode}/', dest='pattern',
	                    help='The URI to download from. Is a python format string with series and episode passed. You probably don\'t need to change this.')
	parser.add_argument('-o', '--output-file-pattern', default='{episode}.mp4', dest='output',
	                    help='The pattern to use for generating file names. Is a python format string with series and episode passed.')
	parser.add_argument('-u', '--user-agent', default='Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0', dest='uagent',
	                    help='The User-Agent to use')
	parser.add_argument('-w', '--no-wget', action='store_const', const=True, default=False, dest='wget',
	                    help='Setting this flag forces OtakuSCRAPE to use the built in downloader instead of wget')
	parser.add_argument('-q', '--quiet', action='store_const', const=True, default=False, dest='quiet', help='Do not print logs')
	parser.add_argument('-s', '--shellcode', action='store_const', const=True, default=False, dest='shellcode',
	                    help='Just print out the shellcode required to perform the downloads, instead of actually downloading anything.')

	args = parser.parse_args()

	URI_TEMPLATE = args.pattern
	USER_AGENT = args.uagent
	OUTPUT_FILE_TEMPLATE = args.output
	SHELLCODE = args.shellcode
	QUIET = args.quiet or SHELLCODE

	command = args.command

	quality = args.quality

	if quality not in {'HIGHEST', 'LOWEST'}:
		try:
			quality = int(quality)
			if quality <= 0:
				raise ValueError(str(quality))

		except ValueError:
			print("OtakuSCRAPE: Invalid Quality: quality must be 'HIGHEST', 'LOWEST', or a positive integer", file=sys.stderr)
			sys.exit(1)
	
	if args.wget:
		WGET = False

	if command == 'download':
		download_episodes(args.anime, args.episodes, quality)
	
	elif command == 'search':
		search_anime(args.anime)
