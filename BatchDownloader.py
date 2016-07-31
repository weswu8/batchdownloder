#!/usr/bin/python
# -*- coding: utf-8 -*-

# version 1.0 2015.09.07

from tkinter import *
from tkinter import ttk
import os, time
import configparser
from http.client import HTTPSConnection, HTTPConnection
from base64 import b64encode
import threading

#==================Function Define =====================================
#==================define the global variables ========================
# the input file which contain the url list
mInputFile = ''
# the ms of the sleep for the main loop
mSleepMS = ''
# the configuration file for the tools
mConfFile = 'batchdownloader.cfg'
# the pool size for the container which hold the target url
mPoolSize = 5000
# the flag to stop download task
mStop = False
# he flag to pause or resume the running downloading loop
mPause = False
# the target path that will store the downloaded files
mSavePath = 'C:/My Documents/My Dev/GrokCrawler'
# the total numbers of the current task
mTotalNum = 0
# the number of the task processed
mProcessed = 0
# the number of success
mSuccess = 0
# the number of failed
mFailed = 0
# the current checkpoint in the task list
mCurrentPOS = 0
# the full URL list wait for downloading
mUrlList = []
# the username for https authentication
mUserName = ''
# the password for https authentication
mPassword = ''
# the log file for the task
mLogFile = ''
# the Statistics file for the task
mStatFile = ''
# the directory which will store the log file
mLogsDir = ''
# initialize the configuration file, put the default setting, currently support below keys
# inputfile, the file which include the URL to be downloaded
# sleepms, the ms for the main loop
# poolsize, the pool size for the container which hold the target url
# savepath, the target path that will store the downloaded files, i.e C:/My Documents/My Dev/GrokCrawler
def init_config_file():
    if os.path.exists(mConfFile):
        return
    mConfig = configparser.ConfigParser()
    mConfig['DEFAULT'] = {'inputfile': '',
                           'sleepms': 100,
                           'poolsize': '',
                           'savepath': '',
                           'username': '',
                           'password': '',
                           'logfile': '',
                           'statfile': ''
                          }
    with open(mConfFile, 'w') as configfile:
        mConfig.write(configfile)

# read the specific key from the configuration file
def read_config_by_key(mConfFile, mKey):
    mConfig = configparser.ConfigParser()
    #messagebox.showinfo(mKey)
    mConfig.read(mConfFile)
    return mConfig.get('DEFAULT', mKey)

# update the value for the specific key
# **keyv : AutoLogin='False'
def change_config_by_key(mConfFile, section, **keyv):
    mConfig = configparser.ConfigParser()
    mConfig.read(mConfFile)
    [mConfig.set(section, key, keyv[key]) for key in keyv if mConfig.has_option(section, key)]
    mConfig.write(open(mConfFile, 'w'))

# update the gui console
def update_gui_input():
    global gInputFile, gSavePath, gSleepMS
    global mInputFile, mSavePath, mSleepMS
    gInputFile.delete(0, END)
    gInputFile.insert(0,mInputFile)
    gSavePath.delete(0, END)
    gSavePath.insert(0,mSavePath)
    gSleepMS.delete(0, END)
    gSleepMS.insert(0,mSleepMS)

    show_message_info("The value is updated!")

# update the TargetFile value
def update_inputfile_value():
    global mConfFile
    newFileName = gInputFile.get()
    oldFileName = read_config_by_key(mConfFile, 'inputfile')
    if newFileName == '':
        return
    change_config_by_key(mConfFile, 'DEFAULT', inputfile = newFileName)
    # update the global variables
    update_global_var()
    # Just refresh the variables
    if newFileName == oldFileName:
        return
    # create log directory
    #if not os.path.exists(mLogsDir):
    #   os.makedirs(mLogsDir)
    # create the statistics file
    create_stat_file()
    # create the error log file
    create_log_file()
    # update the global variables
    update_global_var()
    # refresh the gui input filed
    update_gui_input()
    # refresh the statistic
    read_stat_file()
    # update the GUI console
    update_gui_stat("")
    # show the message
    show_message_info("The value of input file is updated!")

# update the TargetFile value
def update_savepath_sleepms():
    global mConfFile
    newSleepMS = gSleepMS.get()
    newSavePath = gSavePath.get().replace("\\","/")
    if newSleepMS == 0 and newSavePath == '':
        return
    change_config_by_key(mConfFile, 'DEFAULT', sleepms = newSleepMS)
    change_config_by_key(mConfFile, 'DEFAULT', savepath = newSavePath)
    # update the global variables
    update_global_var()
    # refresh the gui input filed
    update_gui_input()

# read and update the global variable in memory
def update_global_var():
    global mConfFile, mInputFile, mLogFile, mStatFile, mLogsDir
    global mSleepMS, mSavePath, mPoolSize, mUserName, mPassword
    mConfig = configparser.ConfigParser()
    mConfig.read(mConfFile)
    mInputFile = mConfig.get('DEFAULT', 'inputfile')
    mSleepMS = mConfig.getint('DEFAULT','sleepms')
    mSavePath = mConfig.get('DEFAULT', 'savepath')
    mPoolSize = mConfig.get('DEFAULT', 'poolsize')
    mUserName = mConfig.get('DEFAULT', 'username')
    mPassword = mConfig.get('DEFAULT', 'password')
    mLogFile = mConfig.get('DEFAULT', 'logfile')
    mStatFile = mConfig.get('DEFAULT', 'statfile')
    mLogsDir = mSavePath + '/logs'

# read the url list from the file ,and store them in the list.
# ['https://','https://']
# result[0] ,get the url for 1st item
def get_url_list(inputfile):
    global mTotalNum,mUrlList
    mUrlList = [line.strip() for line in open(mInputFile, 'r')]
    #return mUrlList

# parse the URL, and store the result in the dictionary
def url_path_to_dict(path):
    pattern = (r'^'
               r'((?P<schema>.+?)://)?'
               r'((?P<user>.+?)(:(?P<password>.*?))?@)?'
               r'(?P<host>.*?)'
               r'(:(?P<port>\d+?))?'
               r'(?P<path>/.*?)?'
               r'(?P<query>[?].*?)?'
               r'$'
               )
    regex = re.compile(pattern)
    m = regex.match(path)
    d = m.groupdict() if m is not None else None
    return d

# create the folder structure for the target file
# pathurl : /raw/aax/dd/a.java
def create_full_directory(pathurl):
    global mSavePath
    mDirectory = mSavePath + os.path.split(pathurl)[0]
    if os.path.exists(mDirectory) is not True:
        try:
            os.makedirs(mDirectory)
        finally:
            return mDirectory

# change the state between pause and resume
def switch_puse_resume():
    global mPause, gPause
    if mPause is True:
        mPause = False
        gPause["text"] = "Pause"
        show_message_info("The task is resuming!")

    else:
        mPause = True
        gPause["text"] = "Resume"
        show_message_info("The task is paused!")

# create the error log  file
def create_log_file():
    global mInputFile, mLogFile, mConfFile,mLogsDir
    mLogFile = mInputFile + '.err'
    open(mLogFile, 'a').close()
    # update the main configure file
    change_config_by_key(mConfFile, 'DEFAULT', logfile = mLogFile)

# put the failed link into the logfile
def log_failed_link(fullurl):
    global mLogFile
    with open(mLogFile, 'a') as file:
        file.write(fullurl +'\n')

# create the statistics file
def create_stat_file():
    global mInputFile, mStatFile, mConfFile
    mStatFile = mInputFile + '.stat'
    mConfig = configparser.ConfigParser()
    mConfig['DEFAULT'] = {'totalnum': 0,
                           'processed': 0,
                           'success': 0,
                           'failed': 0,
                           'currentpos': 0
                          }
    with open(mStatFile, 'w+') as configfile:
        mConfig.write(configfile)
    # update the main configure file
    change_config_by_key(mConfFile, 'DEFAULT', statfile = mStatFile)

# read the statistics form the file
def read_stat_file():
    global mStatFile, mTotalNum, mProcessed, mSuccess, mFailed, mCurrentPOS
    if not os.path.exists(mStatFile):
        return
    mConfig = configparser.ConfigParser()
    mConfig.read(mStatFile)
    mTotalNum = mConfig.getint('DEFAULT', 'totalnum')
    mProcessed = mConfig.getint('DEFAULT', 'processed')
    mSuccess = mConfig.getint('DEFAULT', 'success')
    mFailed = mConfig.getint('DEFAULT', 'failed')
    mCurrentPOS = mConfig.getint('DEFAULT', 'currentpos')

# update the statistics form memory to the file
def update_stat_file():
    global mStatFile, mTotalNum, mProcessed, mSuccess, mFailed, mCurrentPOS
    mConfig = configparser.ConfigParser()
    mConfig['DEFAULT'] = {'TotalNum': mTotalNum,
                           'Processed': mProcessed,
                           'Success': mSuccess,
                           'Failed': mFailed,
                           'CurrentPOS': mCurrentPOS
                          }
    with open(mStatFile, 'w+') as configfile:
        mConfig.write(configfile)

# show response message in the bottom text box
def show_message_info(msg):
    global gCurrentURL
    gCurrentURL.delete(1.0, END)
    gCurrentURL.insert(END, msg)

# update the gui console
def update_gui_stat(curl):
    global mTotalNum, mProcessed, mSuccess, mFailed, mCurrentPOS
    global gTotal, gProcessed, gSuccess, gFailed, gCurrentURL
    gTotal.delete(0, END)
    gTotal.insert(0,mTotalNum)
    gProcessed.delete(0, END)
    gProcessed.insert(0,mProcessed)
    gSuccess.delete(0, END)
    gSuccess.insert(0,mSuccess)
    gFailed.delete(0, END)
    gFailed.insert(0,mFailed)

    show_message_info(curl)

# batch download worker
def bactch_download_worker():
    global mStop, mPause
    global mInputFile, mLogFile, mStatFile, mTotalNum, mProcessed, mSuccess, mFailed, mCurrentPOS
    global mUrlList
    global gProgressbar

    get_url_list(mInputFile)

    # get the check point and start from there
    read_stat_file()
    # show start msg
    show_message_info("The task is starting...")
    mTotalNum = len(mUrlList)
    # begin the main loop
    idx = 0
    #for idx in range(mTotalNum):
    while (idx < mTotalNum):
        if mStop:
            break
        if mPause:
            time.sleep(10)
            continue
        # start form the check point
        if idx < mCurrentPOS:
            idx += 1
            continue
        try:
            mUrl = mUrlList[idx]
            mUrlPattern = url_path_to_dict(mUrl)
            # create the directory
            create_full_directory(mUrlPattern['path'])
            fPath = mSavePath + mUrlPattern['path']
            # handle the https link
            if mUrlPattern['schema'] == 'https':
                #This sets up the https connection
                tHost = mUrlPattern['host']
                if mUrlPattern['port'] != None:
                    tHost = mUrlPattern['host'] + ':' + mUrlPattern['port']
                mConn = HTTPSConnection(tHost)
                #we need to base 64 encode it
                #and then decode it to acsii as python 3 stores it as a byte string
                mAuthStr = mUserName + ":" + mPassword
                userAndPass = b64encode(mAuthStr.encode("utf-8")).decode("ascii")
                headers = { 'Authorization' : 'Basic %s' %  userAndPass }
                tUrl = mUrlPattern['path']
                if mUrlPattern['query'] != None:
                    tUrl = mUrlPattern['path'] + mUrlPattern['query']
                #then connect
                mConn.request('GET', tUrl, headers=headers)
            # handle the http link
            elif mUrlPattern['schema'] == 'http':
                #This sets up the https connection
                tHost = mUrlPattern['host']
                if mUrlPattern['port'] != None:
                    tHost = mUrlPattern['host'] + ':' + mUrlPattern['port']
                mConn = HTTPConnection(tHost)
                tUrl = mUrlPattern['path']
                if mUrlPattern['query'] != None:
                    tUrl = mUrlPattern['path'] + mUrlPattern['query']
                #then connect
                mConn.request('GET', tUrl)
            else:
                continue

            #get the response back
            mRes = mConn.getresponse()
            # at this point you could check the status etc
            # this gets the page text
            if mRes.status == 200:
                 with open(fPath, 'wb') as f:
                     f.write(mRes.read())
                     mSuccess += 1
            else:
                 mFailed += 1
                 log_failed_link(mUrl)

        except Exception as e:
            pass
        finally:

            idx += 1
            mProcessed += 1
            mCurrentPOS += 1

            #update the global variables
            update_global_var()

            #update the statistics file
            update_stat_file()

            # update the gui console
            update_gui_stat(mUrl)

            # update the progressbar
            gProgressbar['value'] = (mProcessed/mTotalNum) * 100

        # sleep the loop
        if mSleepMS == 0 :
            newSleepSec = 0.01
        else:
            newSleepSec = mSleepMS/1000

        time.sleep(newSleepSec)

    # update the progressbar
    gProgressbar['value'] = (mProcessed/mTotalNum) * 300
    # show the finish msg
    show_message_info("The task is done!")

    # activate the button
    gStart.configure(state=NORMAL)

# in order to avoid to block the main GUI event loop, start the batch downloading task in another thread
def start_downloader_thread():
    global mDownloaderThread, gStart, mInputFile
    if mInputFile == '' or not os.path.exists(mInputFile):
        show_message_info("The input file does not exists!")
        return
    mDownloaderThread = threading.Thread(target=bactch_download_worker)
    mDownloaderThread.daemon = True
    mDownloaderThread.start()
    # avoid the start new thread
    gStart.configure(state=DISABLED)

#=============Begin the main logic =====================
# create and read the configuration
init_config_file()

# update the global variable based on the configuration
update_global_var()

# read the statistics file, and update the variable in memory
read_stat_file()

#=========== end the main logic =========================

#=============GUI Design ===============================
root = Tk()
root.geometry('435x300+300+300')
root.resizable(0, 0)
root.title('Batch Downloader by wesley')


Label(root, text="Input File:").grid(row=0, column=0, sticky='e')
gInputFile = Entry(root, width=40)
gInputFile.grid(row=0, column=1, padx=2, pady=2, sticky='we', columnspan=9)
gInputFile.insert(0,mInputFile)

Label(root, text="Save Path:").grid(row=1, column=0, sticky='e')
gSavePath = Entry(root, width=15)
gSavePath.grid(row=1, column=1, padx=2, pady=2, sticky='we', columnspan=2)
gSavePath.insert(0,mSavePath)

Label(root, text="Sleep(ms):").grid(row=1, column=3, sticky='e')
gSleepMS = Entry(root, width=15)
gSleepMS.grid(row=1, column=4, padx=2, pady=2, sticky='we', columnspan=2)
gSleepMS.insert(0,mSleepMS)

Button(root, text="Change", command=update_inputfile_value).grid(row=0, column=10, sticky='e'+'w', padx=2, pady=2)
Button(root, text="Change", command=update_savepath_sleepms).grid(row=1, column=10, sticky='e'+'w', padx=2)

ttk.Separator(root,orient=HORIZONTAL).grid(row=2, columnspan=11,sticky="ew")

Label(root, text="Progress:").grid(row=3, column=0,sticky='w')
gProgressbar = ttk.Progressbar(root, length = 300,value=0)
gProgressbar.grid(row=3, column=1, columnspan=9)


Label(root, text="Total:").grid(row=4, column=0,sticky='w')
gTotal = Entry(root, width=15)
gTotal.grid(row=4, column=1, padx=2, pady=2, sticky='we', columnspan=2)

Label(root, text="Processed:").grid(row=4, column=3,sticky='we')
gProcessed = Entry(root, width=15)
gProcessed.grid(row=4, column=5, padx=2, pady=2, sticky='we', columnspan=2)

gStart = Button(root, text="Start", command=start_downloader_thread)
gStart.grid(row=4, column=10, sticky='e'+'w', padx=2)

Label(root, text="Success:").grid(row=5, column=0,sticky='w')
gSuccess = Entry(root, width=15)
gSuccess.grid(row=5, column=1, padx=2, pady=2, sticky='we', columnspan=2)

Label(root, text="Failed:").grid(row=5, column=3,sticky='w')
gFailed = Entry(root, width=15)
gFailed.grid(row=5, column=5, padx=2, pady=2, sticky='we', columnspan=2)

gPause  = Button(root, text="Pause", command=switch_puse_resume)
gPause.grid(row=5, column=10, sticky='e'+'w', padx=2)

Label(root, text="Msg:").grid(row=6, column=0,sticky='w')
gCurrentURL = Text(root, width=5, height=10)
gCurrentURL.grid(row=6, column=1, padx=2, pady=2, sticky='we', columnspan=9)


#=============Begin the main logic =====================
# update the gui console
update_gui_stat("Welcome!")
#=========== end the main logic =========================
root.mainloop()