import sqlite3 as sqlite
import os
from Utils import *

iphoneBackupDir = "IphoneBackup"
m_nsAliasName = "wxid_t798rxqmvz7s11"

PARSED_DB_PATH = "DataStore/Contact.db"
PARSED_DATA_CONNECTION = ConnectNonEncryptedDB(PARSED_DB_PATH)
userAlias, userChatEncryption, userDB = GetUpdateContactInfo(PARSED_DATA_CONNECTION, m_nsAliasName)

def GetUserIphoneDB(userChatEncryption):
    for i in range(4):
        DBName = "message_{}.sqlite".format(i + 1)
        CurrDBConnection = ConnectNonEncryptedDB(os.path.join(iphoneBackupDir, DBName))
        currentDBCursor =CurrDBConnection.cursor()
        currentDBCursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tableList = [table[0] for table in currentDBCursor.fetchall()]
        CurrDBConnection.close()
        if userChatEncryption in tableList:
            return i + 1
    return -1

def UpdateIphoneContactMap():
    parsedDataCursor = PARSED_DATA_CONNECTION.cursor()

    parsedDataCursor.execute("""CREATE TABLE IF NOT EXISTS IphoneParsedContact(
                                m_nsUsrName TEXT PRIMARY KEY, 
                                m_nsRemark TEXT,
                                m_nsAliasName TEXT,
                                chat_md5ID TEXT,
                                db_Stored INTEGER
                                );""")
    PARSED_DATA_CONNECTION.commit()
    
    parsedDataCursor.execute("""SELECT m_nsUsrName, m_nsRemark, m_nsAliasName, chat_md5ID
                                FROM ParsedContact;""")
    contactData = parsedDataCursor.fetchall()

    for contact in contactData:
        m_nsUsrName = contact[0]
        m_nsRemark = contact[1]
        m_nsAliasName = contact[2]
        chat_md5ID = contact[3]
        db_Stored = GetUserIphoneDB(chat_md5ID)
        parsedDataCursor.execute("""INSERT OR REPLACE INTO IphoneParsedContact(
                                    m_nsUsrName,
                                    m_nsRemark, 
                                    m_nsAliasName, 
                                    chat_md5ID,
                                    db_Stored)
                                    VALUES(?,?,?,?,?);""", (m_nsUsrName, m_nsRemark,
                                    m_nsAliasName, chat_md5ID, db_Stored))

        contactRemark = m_nsRemark if type(m_nsRemark) is not None or len(m_nsRemark.replace(" ", "")) > 1 else m_nsUsrName
        print("Contact {} Stored in DB {}".format(contactRemark, db_Stored))

    PARSED_DATA_CONNECTION.commit()

UpdateIphoneContactMap()





