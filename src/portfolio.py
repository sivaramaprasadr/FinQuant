import pandas as pd
class Fund(object):
    ''' Object that contains information about a fund.
    To initialise the object, it requires a name, information about
    the fund given as one of the following data structures:
     - pandas.Series
     - pandas.DataFrame
    The investment information should normally contain labels such as
     - Name
     - Year
     - Strategy
     - CCY
     - FMV
    It also requires daily return of investments (ROI) as a pandas.DataFrame or
    pandas.Series. If it is a DataFrame, the "roi_data" data structure is required
    to contain the following label
     - ROI
    '''
    def __init__(self, investmentinfo, roi_data):
        self.name = investmentinfo.Name
        self.investmentinfo = investmentinfo
        self.roi_data = roi_data
    def getInvestmentInfo(self):
        return self.investmentinfo
    def getRoiData(self):
        return self.roi_data
    def compSkew(self):
        return self.roi_data.skew().values[0]
    def compKurtosis(self):
        return self.roi_data.kurt().values[0]
    def __str__(self):
        return str(pd.DataFrame([self.investmentinfo]))

class Portfolio(object):
    ''' Object that contains information about a investment portfolio.
    To initialise the object, it requires a name, reference year.
    To fill the portfolio with investment information and daily return of investments
    (ROI) data, the function addFund(fund) should be used, in which `fund` is a `Fund`
    object. a pandas.DataFrame
    of the portfolio investment information. The corresponding daily return of investments
    (ROI) are stored in the Fund object.
    '''
    def __init__(self, name, ref_year):
        # initilisating instance variables
        self.name = name
        self.ref_year = ref_year
        # initialise some more instance variables that do not have a value yet
        self.portfolio = pd.DataFrame()
        self.funds = {}
        self.pf_roi_data = pd.DataFrame()
        self.pf_means = None
        self.pf_weights = None
        self.expectedRoi = None
        self.volatility = None
        self.covPf = None

    def addFund(self, fund):
        # adding fund to dictionary containing all funds provided
        self.funds.update({fund.name : fund})
        # adding information of fund to the portfolio
        self.portfolio = self.portfolio.append(fund.getInvestmentInfo(), ignore_index=True)
        # also add ROI data of fund to the dataframe containing all roi data points
        self.__addRoiData(fund.name, fund.roi_data.ROI)

    def __addRoiData(self, name, df):
        # get length of columns in pf_roi_data, in order to create a new column
        cols = len(self.pf_roi_data.columns)
        # add roi data to overall dataframe of roi data:
        self.pf_roi_data.insert(loc=cols, column=name, value=df.values)#, inplace=True)#, ignore_index=True)

    # get functions:
    def getPortfolio(self):
        return self.portfolio

    def getRefYear(self):
        return self.ref_year

    def getPfRoiData(self):
        return self.pf_roi_data

    def getFund(self, name):
        return self.getFunds()[name]

    def getFunds(self):
        return self.funds

    def getPfMeans(self):
        return self.pf_means

    def getPfWeights(self):
        return self.pf_weights

    def getPfExpectedRoi(self):
        return self.expectedRoi

    def getVolatility(self):
        return self.volatility

    def getCovPf(self):
        return self.covPf

    # set functions:
    def setPfMeans(self, pf_means):
        self.pf_means = pf_means

    def setPfWeights(self, pf_weights):
        self.pf_weights = pf_weights

    def setPfExpectedRoi(self, expectedRoi):
        self.expectedRoi = expectedRoi

    def setVolatility(self, volatility):
        self.volatility = volatility

    def setCovPf(self, covPf):
        self.covPf = covPf

    # functions to compute quantities
    def compPfMeans(self):
        pf_means = self.getPfRoiData().mean().values
        # set instance variable
        self.setPfMeans(pf_means)
        return pf_means

    def compPfWeights(self):
        import numpy as np
        # computes the weights of the funds in the given portfolio
        # in respect of the total investment
        total = self.portfolio.FMV.sum()
        pf_weights = self.portfolio.FMV/total
        # set instance variable
        self.setPfWeights(pf_weights)
        return pf_weights

    def compPfExpectedRoi(self):
        # computing portfolio ROI
        pf_means = self.compPfMeans()
        pf_weights = self.compPfWeights()
        expectedRoi = weightedMean(pf_means, pf_weights)
        # set instance variable
        self.setPfExpectedRoi(expectedRoi)
        return expectedRoi

    def compPfVolatility(self):
        # computing the volatility of a portfolio
        pf_weights = self.compPfWeights()
        covPf = self.compCovPf()
        volatility = weightedStd(covPf, pf_weights)
        # set instance variable
        self.setVolatility(volatility)
        return volatility

    def compCovPf(self):
        # get the covariance matrix of the roi of the portfolio
        covPf = self.pf_roi_data.cov()
        # set instance variable
        self.setCovPf(covPf)
        return covPf

    def compSharpe(self, riskfreerate):
        expected_roi = self.getPfExpectedRoi()
        volatility = self.getVolatility()
        return SharpeRatio(expected_roi, riskfreerate, volatility)

    def __str__(self):
        return str(self.getPortfolio())

class PortfolioBKUP(object):
    ''' Object that contains information about a investment portfolio.
    To initialise the object, it requires a name, reference year, a pandas.DataFrame
    of the portfolio investment information. The corresponding daily return of investments
    (ROI) are stored in the Fund object.
    '''
    def __init__(self, name, ref_year, portfolio, raw_data):
        self.name = name
        self.ref_year = ref_year
        self.portfolio = pd.DataFrame(portfolio)
        self.raw_data = pd.DataFrame(raw_data)
        # add column "Age" to dataframe:
        self.addAge()
        self.pf_roi_data = self.extractPfRoiData()
        self.funds = self.extractFunds()

    def addAge(self):
        if (not 'Age' in self.portfolio.columns):
            idx = self.portfolio.columns.get_loc('Year')
            self.portfolio.insert(loc=idx+1, column='Age',
                                  value=self.getRefYear()-self.portfolio['Year'].values)

    def extractPfRoiData(self):
        # get dictionary that holds relevant information to extract 
        # data from the raw dataset:
        d = {}
        for i in range(len(self.portfolio.index)):
            d.update({self.portfolio.Name[i] : {'Age' : self.portfolio.Age[i],
                                                'Strategy' : self.portfolio.Strategy[i]}})
        # generate a string to query the relevant data:
        querystring = ''
        for key, value in d.items():
            querystring = querystring+'Age=='+str(value['Age'])+' & Strategy=="'+str(value['Strategy'])+'" | '
        # remove trailing ' | ' from querystring
        querystring = querystring[:-3]
        # get data for the given portfolio:
        pf_roi_data = self.getRawData().query(querystring).reset_index(drop=True)
        return pf_roi_data

    def extractFunds(self):
        funds = {}
        for i in range(len(self.portfolio.index)):
            name = self.portfolio.Name[i]
            age = self.portfolio.Age[i]
            strategy = self.portfolio.Strategy[i]
            if ('Name' in self.pf_roi_data.columns):
                querystring = 'Name=='+str(name)
            elif (all(x in self.pf_roi_data.columns for x in ['Age', 'Strategy'])):
                None
            #elif ('Age' in self.pf_roi_data.columns):
            #roi_data = 
            roi_data = []
            funds.update({name : {'Age' : age,
                                  'Strategy' : strategy,
                                  'ROI' : roi_data}})
        return funds

    def addFund(self, fund):
        #self.funds.update({fund.name : fund})
        self.portfolio = self.portfolio.append(fund.getInvestmentInfo(), ignore_index=True)
                                              #self.funds[key].getInvestmentInfo(), ignore_index=True)

    #def plotFundsRoi(self):
    #    #for

    #def plotFundRoi(self):
    #    

    #def getPortfolio(self):
    #    df = pd.DataFrame()
    #    for key in self.funds.keys():
    #        df = df.append(self.funds[key].getInvestmentInfo(), ignore_index=True)
    #    return df
    #    #return pd.DataFrame.from_dict(self.funds, orient='index', columns=["ID","Fund","Vintage","Region","Strategy","CCY","FMV"])
    #    #return pd.DataFrame.from_dict(self.funds, orient='index')
    #    #return pd.DataFrame(self.funds)
    #    #pd.DataFrame.from_dict(data, orient='index',
    #    #                  columns=['A', 'B', 'C', 'D'])
    def getRefYear(self):
        return self.ref_year
    def getPortfolio(self):
        return self.portfolio
    def getRawData(self):
        return self.raw_data
    def getPfRoiData(self):
        return self.pf_roi_data
    def getFund(self, name):
        fund = self.getPortfolio().loc[self.getPortfolio()['Name'] == name]
        return fund
    def __str__(self):
        return str(self.getPortfolio())

def weightedMean(means, weights):
    import numpy as np
    return np.sum(means * weights)

def weightedStd(cov_matrix, weights):
    import numpy as np
    weighted_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return weighted_std

def SharpeRatio(exproi, riskfreerate, volatility):
    sharpe = (exproi - riskfreerate)/float(volatility)
    return sharpe