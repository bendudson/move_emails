#!/usr/bin/env python
# -------------------------------------------------------
# 
# Move emails between IMAP servers
#
# move_emails(FromHost, FromUser, FromPassword, FromBox
#             ToHost, ToUser, ToPassword, ToBox,
#             NMove)
#
# Moves the oldest <NMove> emails from FromHost to ToHost
#
# *Host     - The IMAP host name    (string)
# *User     - User name on Host (string)
# *Password - Password on Host (string). None or "" will prompt
# *Box      - The mailbox to use
#
# By default uses "Inbox" on both servers, but to change this
#
# If you're using this script more than once, you can fill in
# the details and won't be prompted
#
# B.Dudson
# Oct 2011
#

import os, sys, getpass, time, readline
import email, email.Errors, email.Header, email.Message, email.Utils
import imaplib

NMove = None # How many messages to move? prompts if None

FromHost = None # host to move emails from. Prompts if None
FromUser = None
FromPassword = None
FromBox = "Inbox"

ToHost = None
ToUser = None
ToPassword = None
ToBox = "Inbox"

def error(reason):
    sys.stderr.write('%s\n' % reason)
    sys.exit(1)

def connectToServer(host, user, password, ssl):
    print 'Connecting to %s...' % (host)
    try:
        if ssl:
            mbox = imaplib.IMAP4_SSL(host)
        else:
            mbox = imaplib.IMAP4(host)

    except:
        typ,val = sys.exc_info()[:2]
        error('Could not connect to IMAP server "%s": %s'
              % (host, str(val)))
    
    if user or mbox.state != 'AUTH':
        user = user or getpass.getuser()
    if (password == "") or (password == None):
        pasw = getpass.getpass("Please enter password for %s on %s: "
                               % (user, host))
    else:
        pasw = password
    
    try:
        typ,dat = mbox.login(user, pasw)
    except:
        typ,dat = sys.exc_info()[:2]

    if typ != 'OK':
        error('Could not open INBOX for "%s" on "%s": %s'
              % (user, host, str(dat)))
    return mbox

def move_emails(FromHost, FromUser, FromPassword, FromBox,
                ToHost, ToUser, ToPassword, ToBox, 
                NMove):
    ToMbox   = connectToServer(ToHost, ToUser, ToPassword, True)
    ToMbox.select(ToBox)
    FromMbox = connectToServer(FromHost, FromUser, FromPassword, False)
    FromMbox.select(FromBox)
    
    FromMbox.expunge()
    
    # Sort by date
    typ, sort = FromMbox.sort('DATE', 'UTF-8', 'ALL')
    
    nums = sort[0].split()
    
    for i in range(NMove):
        n = nums[i]
        # Get some header information
        typ, data = FromMbox.fetch(n, '(BODY[HEADER.FIELDS (from subject date)])')
        print 'Message %s\n%s\n' % (n, data[0][1])
        
        # Get the full data
        typ, data = FromMbox.fetch(n, '(RFC822)')
        
        # Upload to server
        ToMbox.append(ToBox, '(\\Seen)', None, data[0][1])
        
        # Delete from original
        FromMbox.store(n, "+FLAGS.SILENT", '(\\Deleted)')
    
    FromMbox.close()
    FromMbox.logout()
    
    ToMbox.close()
    ToMbox.logout()

if __name__ == '__main__':
    try:
        if FromHost == None:
            FromHost = raw_input("From Host: ")
        if FromBox == None:
            FromBox = raw_input("From mail box: ")
        if FromUser == None:
            FromUser = raw_input("Username on "+FromHost+": ")
        if ToHost == None:
            ToHost = raw_input("To Host: ")
        if ToBox == None:
            ToBox = raw_input("To mail box: ")
        if ToUser == None:
            ToUser = raw_input("Username on "+ToHost+": ")
        if NMove == None:
            while(True):
                try:
                    s = raw_input("Number of emails to move: ")
                    NMove = int(s)
                    break
                except:
                    pass
        
        move_emails(FromHost, FromUser, FromPassword, FromBox,
                    ToHost, ToUser, ToPassword, ToBox, 
                    NMove)
    except KeyboardInterrupt:
        pass
