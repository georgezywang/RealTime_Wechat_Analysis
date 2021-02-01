import ConnectWXDB
import datetime
import DataPlotter
import os
import sys
import time
from pysqlcipher3 import dbapi2 as sqlite
import hashlib
import argparse
import matplotlib.pyplot as plt
from colorama import Fore, Style

class ChatProcess():
    def __init__(self, m_nsAliasName):
        self.m_nsAliasName = m_nsAliasName
        self.myLastReply = datetime.datetime.timestamp(datetime.datetime.now())
        self.contactLastReply = datetime.datetime.timestamp(datetime.datetime.now())
        self.contactReplyInterval = []
        self.myReplyInterval = []
        self.startTime = datetime.datetime.now()
        self.lastFetchTime = datetime.datetime.now()
        self.lastReplyEntity = -1 # 0 is me, one is contact
        self.ParsePastChatDistribution()

    def ProcessUpdateHistory(self, updateChatHistory):
        for logMsg in updateChatHistory:
            msgCreateTime = logMsg[1]
            mesDes = logMsg[6]

            if mesDes == 0:
                if self.lastReplyEntity == -1:
                    self.startTime = datetime.datetime.now()
                else:
                    self.myReplyInterval.append(msgCreateTime - max(self.myLastReply, self.contactLastReply))
                self.myLastReply = float(msgCreateTime)    
                self.myMsgCountMonthly[-1] += 1  
                self.myMsgCountDaily[-1] += 1 
                self.lastReplyEntity = 0
            else:
                if self.lastReplyEntity == -1:
                    self.startTime = datetime.datetime.now()
                else:
                    self.contactReplyInterval.append(msgCreateTime -max(self.myLastReply, self.contactLastReply))
                self.contactLastReply = msgCreateTime
                self.contactMsgCountMonthly[-1] += 1  
                self.contactMsgCountDaily[-1] += 1 
                self.lastReplyEntity = 1
    
    def ParsePastChatDistribution(self):
        self.myMsgTimeMonthly, self.myMsgCountMonthly, self.myMsgTimeDaily, self.myMsgCountDaily = DataPlotter.GetChatHistoryDistribution(PARSED_DATA_CONNECTION, self.m_nsAliasName, 0)
        self.contactMsgTimeMonthly, self.contactMsgCountMonthly, self.contactMsgTimeDaily, self.contactMsgCountDaily = DataPlotter.GetChatHistoryDistribution(PARSED_DATA_CONNECTION, self.m_nsAliasName, 1)
    
    def AnimateAnalysis(self):
        DataPlotter.PlotStats(self.myMsgTimeMonthly, self.myMsgCountMonthly, self.myMsgTimeDaily, self.myMsgCountDaily, self.contactMsgCountMonthly, self.contactMsgCountDaily, self.contactReplyInterval, self.myReplyInterval, self.m_nsAliasName, self.startTime, self.myLastReply, self.contactLastReply)
    
    def PrintChatSummary(self):
        print(Fore.RED)
        print("Chat Ended")
        chatTime = datetime.datetime.timestamp(datetime.datetime.now()) - datetime.datetime.timestamp(self.startTime)
        myMsgCount = len(self.myReplyInterval)
        contactMsgCount = len(self.contactReplyInterval)
        if (contactMsgCount < 1 or myMsgCount < 1):
            print("\nMessage Insufficient".format())
            print(Style.RESET_ALL)
            sys.exit()
        
        print(Style.RESET_ALL)
        myMsgReplyPeriod = "{0:.4g}".format(sum(self.myReplyInterval) / myMsgCount)
        contactMsgReplyPeriod = "{0:.4g}".format(sum(self.contactReplyInterval) / contactMsgCount)
        myLongestWait = "{0:.4g}".format(max(self.contactReplyInterval))
        myLongestHold =  "{0:.4g}".format(max(self.myReplyInterval))

        print(Fore.BLUE)
        print("\nThis chat lasts {}s\nWith me sending {} messages\n{} sennding {} messages".format(int(chatTime), myMsgCount, self.m_nsAliasName, contactMsgCount))
        print("On average, I reply with period {}s\n{} replies with period {}s".format(myMsgReplyPeriod, self.m_nsAliasName, contactMsgReplyPeriod))
        print("My longest wait is {}s\nMy longest hold is {}s\n".format(myLongestWait, myLongestHold))
        print(Style.RESET_ALL)

#Utils
def ReadKey(KeyPath):
    with open(KeyPath, "r") as fp:
        DBKey  = fp.read()
        DBKey = DBKey[2:]
    return DBKey

def ConnectNonEncryptedDB(DBPath):
    conn = sqlite.connect(DBPath)
    return conn

def transmd5(stringCode):
    #encrypt string with md5 encryption
	m = hashlib.md5(stringCode.encode(encoding='UTF-8')).hexdigest()
	return(m)

#data retrieval
def UpdateContactMap():
    #Update ParsedContact Table in ParsedDB
    DBKey = ReadKey(KEY_PATH)
    DBCursor = ConnectWXDB.ConnectWXDB(CONTACT_DB_PATH, DBKey)

    DBCursor.execute("""SELECT m_nsUsrName, m_nsRemark, m_nsAliasName
                        FROM WCContact
                        WHERE m_uiCertificationFlag = 0;""")
    contactData = DBCursor.fetchall()

    parsedDataCursor = PARSED_DATA_CONNECTION.cursor()
    parsedDataCursor.execute("""CREATE TABLE IF NOT EXISTS ParsedContact(
                                m_nsUsrName TEXT PRIMARY KEY, 
                                m_nsRemark TEXT,
                                m_nsAliasName TEXT,
                                chat_md5ID TEXT,
                                db_Stored INTEGER
                                );""")

    for contact in contactData:
        m_nsUsrName = contact[0]
        m_nsRemark = contact[1]
        m_nsAliasName = contact[2]
        m_nsAliasName = m_nsUsrName if (m_nsAliasName is None or len(m_nsAliasName) < 1) else m_nsAliasName
        WXDBChat_Prefix = "Chat_"
        chat_md5ID = WXDBChat_Prefix + transmd5(m_nsUsrName)
        db_Stored = -1

        for WXDBIndex in range(10):

            DBName = "msg_{}.db".format(WXDBIndex)
            currentDB = os.path.join(WXDB_DIR, DBName)
            currentDBCursor = ConnectWXDB.ConnectWXDB(currentDB, DBKey)
            currentDBCursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tableList = [table[0] for table in currentDBCursor.fetchall()]
            currentDBCursor.close()

            if chat_md5ID in tableList:
                db_Stored = WXDBIndex
                continue
        
        if db_Stored == -1:
            #print("No Previous History")
            continue
        else:
            contactRemark = m_nsRemark if len(m_nsRemark) > 0 else m_nsUsrName
            print("Contact {} Stored in DB {}".format(contactRemark, db_Stored))
        
        parsedDataCursor.execute("""INSERT OR REPLACE INTO ParsedContact(
                                    m_nsUsrName,
                                    m_nsRemark, 
                                    m_nsAliasName, 
                                    chat_md5ID,
                                    db_Stored)
                                    VALUES(?,?,?,?,?);""", (m_nsUsrName, m_nsRemark,
                                    m_nsAliasName, chat_md5ID, db_Stored))
    PARSED_DATA_CONNECTION.commit()
    parsedDataCursor.close()

def FetchContactData(m_nsAliasName, parsedDataCursor):
    #fetch user data from ParsedContact table
    parsedDataCursor.execute("""SELECT m_nsRemark,
                                chat_md5ID,
                                db_Stored
                                FROM ParsedContact
                                WHERE m_nsAliasName = ?""", (m_nsAliasName, ))
    retreivedInfo = parsedDataCursor.fetchall()
    return retreivedInfo

def GetUpdateContactInfo(m_nsAliasName):
    #Get user info from ParsedContact table
    parsedDataCursor = PARSED_DATA_CONNECTION.cursor()
    userStorageInfo= FetchContactData(m_nsAliasName, parsedDataCursor)

    if len(userStorageInfo) < 1:
        UpdateContactMap()
        retreivedInfo = FetchContactData(m_nsAliasName, parsedDataCursor)
        if len((retreivedInfo)) < 1:
            raise Exception("No Chat History for {} Found".format(m_nsAliasName))
    
    userStorageInfo = userStorageInfo[0]
    userAlias = userStorageInfo[0]
    userChatEncryption = userStorageInfo[1]
    userDB = userStorageInfo[2]
    return userAlias, userChatEncryption, userDB

def UpdateContactHistory(userChatDBCursor, userChatEncryption, userAlias, log = False):
    #update chat history for specific contact
    parsedDataCursor = PARSED_DATA_CONNECTION.cursor()
    #mesDes (msg destination) 0 is contact, 1 is me
    #msgCreateTime is second since 1970
    parsedDataCursor.execute("""CREATE TABLE IF NOT EXISTS {}(
                                mesLocalID INTEGER PRIMARY KEY,
                                msgCreateTime INTEGER,
                                msgContent TEXT,
                                msgStatus INTEGER,
                                msgImgStatus INTEGER,
                                messageType INTEGER,
                                mesDes INTEGER,
                                msgSource TEXT);""".format(userChatEncryption))

    parsedDataCursor.execute("""SELECT max(mesLocalID)
                                FROM {}""".format(userChatEncryption))
    mostRecentChatID = parsedDataCursor.fetchall()[0][0]
    mostRecentChatID = 0 if type(mostRecentChatID) != int else mostRecentChatID

    userChatDBCursor.execute("""SELECT mesLocalID, 
                                msgCreateTime,
                                msgContent,
                                msgStatus,
                                msgImgStatus,
                                messageType,
                                mesDes,
                                msgSource,
                                msgVoiceText
                                FROM {}
                                WHERE mesLocalID > ?""".format(userChatEncryption),\
                                (mostRecentChatID,))
    updateChatHistory = userChatDBCursor.fetchall()

    for chat in updateChatHistory:
        messageType = chat[5]
        msgVoiceText = chat[8]
        chat = list(chat[0:8])
        chat[2] = msgVoiceText if messageType == 34 else chat[2]
        #type 34 is voice message
        parsedDataCursor.execute("""INSERT INTO {}
                                    VALUES(?,?,?,?,?,?,?,?)""".format(userChatEncryption), tuple(chat))
        if log:
            logMsgProcessor(chat, userAlias)
        
    PARSED_DATA_CONNECTION.commit()
    return updateChatHistory

def GetUserDB(m_nsAliasName):
    #get the encrypted db that stores user @m_nsAliasName
    userAlias, userChatEncryption, userDB = GetUpdateContactInfo(m_nsAliasName) 
    DBKey = ReadKey(KEY_PATH)
    DBName = "msg_{}.db".format(userDB)
    userChatDB = os.path.join(WXDB_DIR, DBName)
    userChatDBCursor = ConnectWXDB.ConnectWXDB(userChatDB, DBKey)
    return userChatDBCursor, userChatEncryption, userAlias

def UpdateAllContactChatHistory(log = 1):
    parsedDataCursor = PARSED_DATA_CONNECTION.cursor()
    parsedDataCursor.execute("SELECT m_nsAliasName FROM ParsedContact")
    allRecordedContact = parsedDataCursor.fetchall()
    assert log in range(4), Fore.RED + "ERROR: Wrong log level, expect 0 to 3" + Style.RESET_ALL

    for contact in allRecordedContact:
        userChatDBCursor, userChatEncryption, userAlias = GetUserDB(contact[0])
        updateChatHistory = UpdateContactHistory(userChatDBCursor, userChatEncryption, userAlias, log = False if log < 2 else True)
        if (len(updateChatHistory) and (log == 2)) or log == 3:
            print(Fore.CYAN + "User {}, alias {}, md5 encryption {} fetched".format(contact[0], userAlias, userChatEncryption) + Style.RESET_ALL)

def logMsgProcessor(logMsg, userAlias):
    #process log message
    msgCreateTime = logMsg[1]
    msgContent = logMsg[2]
    messageType = logMsg[5]
    mesDes = logMsg[6]
    timeStampString = datetime.datetime.fromtimestamp(msgCreateTime).strftime("%B %d, %Y %I:%M:%S")
    sender = ("对方 " + userAlias) if (mesDes == 1) else "你"
    
    msgDisplay = {
        1 : msgContent,
        3 : "发送了一张图片",
        34 : "发送的语音内容为: " + msgContent if msgContent is not None else "发送了一条语音",
        47 : "发送了一个gif表情包",
        49 : msgContent.replace('\n', ' ') if msgContent is not None else msgContent,
        10000: '撤回了一条消息，手速好快！'
        #TODO: parse message content for case 49
    }
    print("{} 于 {} : {}".format(sender, timeStampString, msgDisplay.get(messageType, msgContent)))

def RealTimeLogging(m_nsAliasName):
    #Real Time Logging
    if LOG_LEVEL > 0:
        print(Fore.GREEN)
        print("Real Time Logging Started")
        print(Style.RESET_ALL)
    userChatDBCursor, userChatEncryption, userAlias = GetUserDB(m_nsAliasName)
    chatProcess = ChatProcess(m_nsAliasName)
    noUpdateTime = datetime.datetime.timestamp(datetime.datetime.now())
    chatProcess.AnimateAnalysis()

    while True:
        try:
            if datetime.datetime.now().day != chatProcess.startTime.day:
                chatProcess.ParsePastChatDistribution()
            updateChatHistory = UpdateContactHistory(userChatDBCursor, userChatEncryption, userAlias, log = LOG_LEVEL)
            nowTimeStamp = datetime.datetime.timestamp(datetime.datetime.now())

            if (len(updateChatHistory) < 1):
                timeSinceMyLastReply = nowTimeStamp - chatProcess.myLastReply
                timeSinceContactLastRepy = nowTimeStamp - chatProcess.contactLastReply

                if (nowTimeStamp - noUpdateTime > 30):
                    noUpdateTime = nowTimeStamp
                    print(Fore.BLUE)
                    lastReplyEntity = chatProcess.m_nsAliasName if chatProcess.lastReplyEntity == 1 else "me"
                    print("Last Reply Entity Is: {}".format(lastReplyEntity))
                    print("Time Since Contact Last Reply: {}".format(timeSinceContactLastRepy))
                    print("Time Since My Last Reply: {}".format(timeSinceMyLastReply))

                    if len(chatProcess.contactReplyInterval) > 5 and timeSinceContactLastRepy > 2 * max(chatProcess.contactReplyInterval) and chatProcess.lastReplyEntity == 0:
                        print(Fore.RED)
                        print("WARNING: Contact is taking usually long time to reply, consider abort chat")
                    elif len(chatProcess.myReplyInterval) > 5 and timeSinceMyLastReply > 2 * max(chatProcess.myReplyInterval) and chatProcess.lastReplyEntity == 1:
                        print(Fore.RED)
                        print("WARNING: You should consider replying to the message")

                    print(Style.RESET_ALL)
                time.sleep(0.5)
                continue

            noUpdateTime = nowTimeStamp
            chatProcess.ProcessUpdateHistory(updateChatHistory)
            chatProcess.AnimateAnalysis()
            time.sleep(1)
            plt.close()
        except KeyboardInterrupt:
            chatProcess.PrintChatSummary()
            sys.exit()
                
if __name__ == "__main__":
    CONTACT_DB_PATH = "/Users/wzy/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/2.0b4.0.9/b309b66a15900f3091dd5d8870f9ecfa/Contact/wccontact_new2.db"
    KEY_PATH = "resources/Key.txt"
    WXDB_DIR = "/Users/wzy/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/2.0b4.0.9/b309b66a15900f3091dd5d8870f9ecfa/Message/"
    PARSED_DB_PATH = "DataStore/Contact.db"
    LOG_LEVEL_MAP = {0 : "NO_CHAT",
                     1 : "REAL_TIME_ONLY",
                     2 : "UPDATE_ONLY",
                     3 : "ALL"}

    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--user_wxid", help = "对方的微信号", required=False)
    parser.add_argument("-u", "--update_all", help = "更新所有备份数据库", action='store_true')
    parser.add_argument("-l", "--logLevel", help = "0 : NO_CHAT, 1 : REAL_TIME_ONLY, 2 : UPDATE_ONLY, 3 : ALL", type = int, default = 1)
    args = parser.parse_args()
    PARSED_DATA_CONNECTION = ConnectNonEncryptedDB(PARSED_DB_PATH)

    LOG_LEVEL = args.logLevel
    print(Fore.BLUE)
    print("Setting LOG_LEVEL To: {}".format(LOG_LEVEL_MAP[LOG_LEVEL]) + Style.RESET_ALL)
    print(Fore.BLUE)
    print("Fetching All Contact History" + Style.RESET_ALL)

    if(args.update_all):
        print(Fore.BLUE)
        print("Updating Contact Map")
        print(Style.RESET_ALL)
        UpdateContactMap()

    UpdateAllContactChatHistory(LOG_LEVEL)
    if(args.user_wxid is not None):
        RealTimeLogging(args.user_wxid)
