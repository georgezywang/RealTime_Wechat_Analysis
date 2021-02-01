import matplotlib
from dateutil.rrule import rrule, MONTHLY
import numpy as np
from scipy.ndimage import gaussian_filter1d
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def GetMonths(start_month, start_year, end_month, end_year):
    start = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)
    return [(d.year, d.month) for d in rrule(MONTHLY, dtstart=start, until=end)]

def GetChatHistoryDistribution(parsedDataConn, m_nsAliasName, mesDes):
    parsedDataCursor = parsedDataConn.cursor()
    parsedDataCursor.execute("""SELECT chat_md5ID
                                FROM ParsedContact
                                WHERE m_nsAliasName = ?""", (m_nsAliasName,))
    chat_md5ID = parsedDataCursor.fetchall()[0]
    assert chat_md5ID is not None, "no history for user {}".format(m_nsAliasName)

    currTime = datetime.now()
    prevYear = currTime.replace(year=currTime.year - 1)
    prevMonth = currTime - timedelta(days = 30)

    oneYearInterval = round(datetime.timestamp(prevYear))
    parsedDataCursor.execute("""SELECT msgCreateTime 
                                FROM {}
                                WHERE msgCreateTime > ?
                                AND mesDes = ? """.format(chat_md5ID[0]), (oneYearInterval, mesDes))
    chatHistoryTimeStamp = parsedDataCursor.fetchall()
    chatHistoryDateTime = [datetime.fromtimestamp(ts[0]) for ts in chatHistoryTimeStamp]

    dtDict = {}
    dailyDict = {}
    for dt in GetMonths(prevYear.month, prevYear.year, currTime.month, currTime.year):
        dtDict[dt] = 0

    while prevMonth <= currTime:
        dailyDict[datetime(prevMonth.year, prevMonth.month, prevMonth.day)] = 0
        prevMonth += timedelta(days=1)

    for dt in chatHistoryDateTime:
        dtDict[(dt.year, dt.month)] += 1
        if datetime(dt.year, dt.month, dt.day) in dailyDict:
            dailyDict[datetime(dt.year, dt.month, dt.day)] += 1
    
    msgTimeMonthly, msgCountMonthly = zip(*sorted(dtDict.items()))
    msgTimeMonthly =[ "{}.{}".format(dateObj[0], dateObj[1]) for dateObj in msgTimeMonthly]
    msgTimeDaily, msgCountDaily = zip(*sorted(dailyDict.items()))
    return list(msgTimeMonthly[-6:]), list(msgCountMonthly[-6:]), list(msgTimeDaily), list(msgCountDaily)

def PlotStats(myMsgTimeMonthly, myMsgCountMonthly, myMsgTimeDaily, myMsgCountDaily, contactMsgCountMonthly, contactMsgCountDaily, contactReplyInterval, myReplyInterval, m_nsAliasName, startTime, myLastReply, contactLastReply):
    msgTimeArray = np.arange(len(myMsgTimeMonthly))
    barWidth = 0.3

    fig, ax = plt.subplots(2, 2)
    monthlyPlot = ax[1, 1]
    rects1 = monthlyPlot.bar(msgTimeArray - barWidth/2, myMsgCountMonthly, barWidth, label='Me')
    rects2 = monthlyPlot.bar(msgTimeArray + barWidth/2, contactMsgCountMonthly, barWidth, label=m_nsAliasName)
    monthlyPlot.set_xticks(msgTimeArray)
    monthlyPlot.set_title("Chat Count Over Past 6 Mo.")
    monthlyPlot.legend()
    monthlyPlot.set_xticklabels(myMsgTimeMonthly)

    dailyPlot = ax[0, 1]
    dailyPlot.plot(myMsgTimeDaily, myMsgCountDaily, label = "Me")
    dailyPlot.plot(myMsgTimeDaily, contactMsgCountDaily, label = m_nsAliasName)
    dailyPlot.set_title("Chat Count Over Past 30 Days")
    dailyPlot.legend()

    convolutionWindowSize = 10
    replyIntervalPlot = ax[0, 0]
    gaussianSigma = 1
    myReplyIntervalConv = gaussian_filter1d(myReplyInterval, gaussianSigma) if len(myReplyInterval) > 0 else myReplyInterval
    contactReplyIntervalConv = gaussian_filter1d(contactReplyInterval, gaussianSigma) if len(contactReplyInterval) > 0 else contactReplyInterval
    replyIntervalPlot.plot(myReplyIntervalConv)
    replyIntervalPlot.plot(contactReplyIntervalConv)

    nowTimeStamp = datetime.timestamp(datetime.now())
    contactPeriod = 'NA' if len(contactReplyInterval) < 1 else int((nowTimeStamp - datetime.timestamp(startTime))/len(contactReplyInterval))
    replyIntervalPlot.set_title("Smooth Real Time Reply Stats: {}".format(contactPeriod))
    # props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    # textstr = "Sec since contact reply: {} \nSec since u reply: {}".format(int(nowTimeStamp - contactLastReply), int(nowTimeStamp - myLastReply))
    # replyIntervalPlot.text(0.05, 0.95, textstr, transform=replyIntervalPlot.transAxes, fontsize=10,
    #     verticalalignment='top', bbox=props)
    
    zoomInPlot = ax[1, 0]
    contactReplyIntervalZoom = contactReplyInterval if len(contactReplyInterval) < convolutionWindowSize else contactReplyInterval[-convolutionWindowSize:]
    myReplyIntervalZoom = myReplyInterval if len(myReplyInterval) < convolutionWindowSize else myReplyInterval[-convolutionWindowSize:]
    zoomInPlot.plot(myReplyIntervalZoom)
    zoomInPlot.plot(contactReplyIntervalZoom)
    zoomInPlot.set_title("Recent Reply Stats")

    for i in range (2):
        for j in range (2):
            for tick in ax[i, j].get_xticklabels():
                tick.set_rotation(30)
    
    fig.tight_layout()
    
    plt.savefig('chatStats.png', bbox_inches='tight')
