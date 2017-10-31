Three point bounding box tool with custom data
===============
Based on 
https://github.com/puzzledqs/BBox-Label-Tool
https://github.com/YenYuHsuan/BBox_with_angle-Label-Tool.git

Installation instructions

Linux:

sudo apt-get install python-pip libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk python-dev

sudo pip install Pillow


Windows:

Install anaconda https://repo.continuum.io/archive/Anaconda3-5.0.1-Windows-x86_64.exe

Open up an anaconda prompt from start menu and go to path with main.py





To Run:

Create a folder called Images at the same level as main.py, put images inside of folder

Then Run:

python main.py

Press Load to load all images

Once labeled, press Next to go to next image and save the current list of bounding box data
