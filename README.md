Batch Downloader
=====
This GUI tool will do the batch download jobs for you, you can give a list of url, and the tool with start the download process and save the file
to the folder.这个图形界面的工具可以根据一个URL列表来批量下载文件。


Feature
====
#####Support HTTP and HTTPS, for HTTPS, you should specify the User/passwd
#####Mulit theads download, better performance
#####Check point of the download process
#####Tracted the failed URL


Support
====
OS:windows
Python : python 3

Installation
====
### step 1.
    sudo pip install tkinter
    down load the tools
### step 2. edit the configuration
    [DEFAULT]
    ; the number of concurrent threads
    poolsize =
    ; log file name
    logfile = CCD.err
    ; statics file name
    statfile = CCD.stat
    ; input file, it should contain a list of url
    inputfile = CCD
    ; the path of your saved file, and it will create the directory tree automatically
    savepath = C:/My Documents/My Dev/GrokCrawler
    ; user for https connection
    username = https.username
    ; passwd for https connection
    password = https.password
    ; sleep time
    sleepms = 5000


### step 3 run
    python you\file\path\BatchDownloader.py
