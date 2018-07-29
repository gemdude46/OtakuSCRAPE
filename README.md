# OtakuSCRAPE
A script for quickly downloading videos off otakustream.tv

## Dependencies
OtakuSCRAPE requires python3 and Beautiful Soup 4.

If python3 is not installed on your system, it will probably be in your package manager.

Beautiful Soup 4 can be installed using pip: `pip3 install beautifulsoup4` or apt if you are on Debian: `apt install python3-bs4`.

Wget is also recommended for more stable downloads.

## Installation
One all the dependencies are installed, just copy the `otakuscrape.py` file to somewhere in your `PATH`.

## Usage
First, search for the sries you want to download. (Movies are not supported at this time.)
Example:

```
otakuscrape search 'future diary'
```

Example output:

```
[...]

Name:       Mirai Nikki 
Id:         mirai-nikki
Episodes:   26
Genres:     Action, Mystery, Psychological, Shounen, Supernatural, Thriller
Premiered:  2011

[...]
```

Search supports english and romanji names.

Next, pass the id and the episodes you want to download to the `download` command.

```
otakuscrape download mirai-nikki {1..26}
```

This will download all episodes of Mirai Nikki to the current directory, name `1.mp4` to `26.mp4` respectively.

You can also change the output destination:

```
otakuscrape download -o 'anime/Mirai Nikki episode {episode}.mp4' mirai-nikki {1..26}
```

`{episode}` will be replaced by the episode number.

OtakuSCRAPE can also output shellcode for downloading videos later:

```
otakuscrape download --shellcode mirai-nikki {1..26}
```
