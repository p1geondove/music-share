# Music share software
I really love music, and sharing music. So a lot of the time when i find a good song that i wanna share i cut up a section in Premiere Pro, add the cover artwork and setup a equalizer and add all metadata and add a soundwave and add a timeline and OMG STOP THATS TOO MUCH...
Yeah maybe theres a way to use templates or automate some things, but at this point i thought "Hey, why not waste like 40 Hours trying to achive the same result in python just to save like 5 minutes every couple of days?"

So this is it. A piece of software you can drag and drop a song into, select start and end of the clip and render a Video. It is focused for Mobile usage, thats why i preset it to horizontal but you can set the resolution

# Controls
| button | action           |
|--------|------------------|
| Space  | pause/play audio |
| R      | render selection |
| LMB    | scrub audio      |
| RMB    | change start/end |
| ESC    | exit             |

# Usage
You can either go get binaries from [here](https://github.com/p1geondove/music-share/releases) or run the code from soure like shown below

### How to run from source

As the arrow of time marches forward i highly suggest using a sophisticated project manager like astral/uv. [Installation](https://docs.astral.sh/uv/getting-started/installation/) of that is super simple, just one line in the terminal. Also you should use git to download the repo, but you can also download the project via your browser

- clone repo (ssh preferred if you have that set up, https is fallback/deprecated)
  - `git clone git@github.com:p1geondove/music-share.git`
  - `git clone https://github.com/p1geondove/music-share.git`
- `cd music-share`
- `uv init`
- `uv add -r requirements.txt`
- optional: activate .venv
  - linux `source .venv/bin/activate`
  - windows `.venv\Scripts\activate.ps1`
- `uv run main.py`

# Dependencies
**YOU NEED FFMPEG FOR RENDERING !**

Get ffmpeg from [here](https://www.ffmpeg.org/download.html)

Its using [pygame](https://pypi.org/project/pygame/) for window/graphics, [numpy](https://pypi.org/project/numpy/) for signal processing, [pillow](https://pypi.org/project/pillow/) for cover art manip, [tinytag](https://pypi.org/project/tinytag/) for extracting metadata and [soundfile](https://pypi.org/project/soundfile/) for reading various audio filetypes and converting them to numpy arrays#

# Dev notes
I also included a quick bash/shell script for builing the project to a executable. In there you will have to change the main dir to your location. Also for that you need to install pyinstaller seperately. To install pyinstaller just run `uv add pyinstaller`