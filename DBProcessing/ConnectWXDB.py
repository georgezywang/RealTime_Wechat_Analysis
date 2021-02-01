from pysqlcipher3 import dbapi2 as sqlite

def ConnectWXDB(DBPath, DBKey):
    conn = sqlite.connect(DBPath)
    c = conn.cursor()
    c.execute("PRAGMA key=\"x'{}'\";".format(DBKey))
    c.execute("PRAGMA cipher_page_size = 1024;")
    c.execute("PRAGMA kdf_iter = 64000;")
    c.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA1;")
    c.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA1;")
    return c