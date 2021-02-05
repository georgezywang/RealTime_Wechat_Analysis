from pysqlcipher3 import dbapi2 as sqlite
import hashlib

def ConnectWXDB(DBPath, DBKey):
    conn = sqlite.connect(DBPath)
    c = conn.cursor()
    c.execute("PRAGMA key=\"x'{}'\";".format(DBKey))
    c.execute("PRAGMA cipher_page_size = 1024;")
    c.execute("PRAGMA kdf_iter = 64000;")
    c.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA1;")
    c.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA1;")
    return c

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


def FetchContactData(m_nsAliasName, parsedDataCursor):
    #fetch user data from ParsedContact table
    parsedDataCursor.execute("""SELECT m_nsRemark,
                                chat_md5ID,
                                db_Stored
                                FROM ParsedContact
                                WHERE m_nsAliasName = ?""", (m_nsAliasName, ))
    retreivedInfo = parsedDataCursor.fetchall()
    return retreivedInfo

def GetUpdateContactInfo(PARSED_DATA_CONNECTION, m_nsAliasName):
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