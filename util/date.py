
class DateUtil:

    @staticmethod
    def cv2Year(dateList):
        year=[]
        for x in dateList:
            year.append(x.year)
        return year
        
    def cv2Month(dateList):
        month=[]
        for x in dateList:
            month.append(x.strftime("%b"))
        return month