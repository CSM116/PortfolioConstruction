import pandas as pd


def drawdown(return_series: pd.Series):
    """Takes a time series of asset returns,
       returns a DataFrame with columns for
       wealth index,
       previous peaks, and
       percentage drawdown"""
    
    wealth_index = 1000*(1+return_series).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks)/previous_peaks
    return pd.DataFrame({"Wealth":wealth_index,
                         "Previous Peak":previous_peaks,
                         "Drawdown": drawdowns})
                         
    
def get_ffme_returns():
    """
    Load the Fama-French Dataset for the returns of the Top and Bottom Deciles by MarketCap
    """
    me_m = pd.read_csv('../data/Portfolios_Formed_on_ME_monthly_EW.csv',header=0,index_col=0,parse_dates=True,na_values=-99.99)
    rets = me_m[['Lo 20','Hi 20']]
    rets.columns = ['SmallCap','LargeCap']
    rets = rets/100
    rets.index = pd.to_datetime(rets.index, format="%Y%m").to_period('M')
    return rets


def get_hfi_returns():
    """
    Load and format the EDHEC Hedge Fund Index Returns
    """
    hfi = pd.read_csv('../data/edhec-hedgefundindices.csv',header=0,index_col=0,parse_dates=True)
    hfi = hfi/100
    hfi.index = hfi.index.to_period('M')
    return hfi

def get_ind_returns():
    """
    Load and format the Ken French 30 Industry Portfolios Value Weighted Montly Returns
    """
    ind = pd.read_csv("../data/ind30_m_vw_rets.csv",header=0, index_col=0,parse_dates=True)/100
    ind.index = pd.to_datetime(ind.index,format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind

def get_ind_size():
    """
    """
    ind = pd.read_csv("../data/ind30_m_size.csv",header=0, index_col=0)
    ind.index = pd.to_datetime(ind.index,format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind

def get_ind_nfirms():
    """
    """
    ind = pd.read_csv("../data/ind30_m_nfirms.csv",header=0, index_col=0)
    ind.index = pd.to_datetime(ind.index,format="%Y%m").to_period('M')
    ind.columns = ind.columns.str.strip()
    return ind


def semideviation(r):
    """
    Returns the semideviation aka negative semideviation of r
    r must be a Series or a DataFrame"""
    is_negative = r<0
    return r[is_negative].std(ddof=0)

def semideviation3(r):
    """
    Returns the semideviation aka negative semideviation of r
    r must be a Series or a DataFrame, else raises a TypeError
    """
    excess= r-r.mean()                                        # We demean the returns
    excess_negative = excess[excess<0]                        # We take only the returns below the mean
    excess_negative_square = excess_negative**2               # We square the demeaned returns below the mean
    n_negative = (excess<0).sum()                             # number of returns under the mean
    return (excess_negative_square.sum()/n_negative)**0.5     # semideviation

def skewness(r):
    """
    Alternative to scipy.stats.skew()
    Computes the skewness of the supplied Series or DataFrame
    Returns a float or a Series
    """
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**3).mean()
    return exp/sigma_r**3
    
def kurtosis(r):
    """
    Alternative to scipy.stats.kurtosis()
    Computes the kurtosis of the supplied Series or DataFrame
    Returns a float or a Series
    """
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**4).mean()
    return exp/sigma_r**4   

import scipy.stats    
def is_normal(r,level=0.01):    
    """
    Applies the Jarque-Bera test to determine if a series is normal or not
    Test is applied at the 1% level by default
    Returns True if the hypothesis of normality is accepted, Flase otherwise
    """
    statistic,p_value = scipy.stats.jarque_bera(r)
    return p_value>level

import numpy as np
def var_historic(r, level=5):
    """
    VaR Historic
    """
    if isinstance(r,pd.DataFrame):
        return r.aggregate(var_historic, level=level)
    elif isinstance(r,pd.Series):
        return -np.percentile(r, level)
    else:
        raise TypeError("Expected r to be a Series or DataFrame")    
    
from scipy.stats import norm
def var_gaussian(r, level=5, modified=False):
    """
    Returns the Parametric Gaussian VaR of a Series or DataFrame
    """
    #compute the Z score assuming it was Gaussian
    z = norm.ppf(level/100)
    if modified:
        #modify the Z score based on observed skewness and kurtosis
        s = skewness(r)
        k = kurtosis(r)
        z = (z +
             (z**2-1)*s/6 +
             (z**3-3*z)*(k-3)/24 -
             (2*z**3-5*z)*(s**2)/36
            )     
    return -(r.mean()+z*r.std(ddof=0))
    
    
def cvar_historic(r,level=5):
    """
    Computes the conditional VaR of a Series or DataFrame
    """
    if isinstance(r,pd.Series):
        is_beyond = r <= -var_historic(r,level=level)
        return -r[is_beyond].mean()
    elif isinstance(r,pd.DataFrame):
        return r.aggregate(cvar_historic,level=level)
    else:
        raise TypeError("Expected Series or DataFrame")

        
def annualize_rets(r, periods_per_year):
    """
    Annualizes a set of returns
    """
    compounded_growth = (1+r).prod()
    n_periods = r.shape[0]
    return compounded_growth**(periods_per_year/n_periods)-1

def annualize_vol(r, periods_per_year):
    """
    Annualizes the vol of a set of returns
    Infering the period per year
    """
    return r.std()*(periods_per_year**0.5)
    
def sharpe_ratio(r, riskfree_rate, periods_per_year):
    """
    Computes the annualized sharpe ratio of a set of returns
    """
    #convert the annual riskfree rate to per period
    rf_per_period = (1+riskfree_rate)**(1/periods_per_year)-1
    excess_ret = r - rf_per_period
    ann_ex_ret = annualize_rets(excess_ret, periods_per_year)
    ann_vol = annualize_vol(r, periods_per_year)
    return ann_ex_ret/ann_vol
    
    
def portfolio_return(weights, returns):
    """
    Weights -> Returns
    """
    return weights.T @ returns

def portfolio_vol(weights, covmat):
    """
    Weights -> Vol
    """
    return (weights.T @ covmat @ weights)**0.5
        
    
def plot_ef2(n_points, er, cov, style=".-"):
    """
    Plots the 2-asset efficient frontier
    """
    if er.shape[0]!=2 or er.shape[0]!=2:
        raise ValueError("plot_ef2 can only plot 2-asset frontiers")
    weights = [np.array([w,1-w]) for w in np. linspace(0,1,n_points)]
    rets = [portfolio_return(w,er) for w in weights]
    vols = [portfolio_vol(w, cov) for w in weights]                   
    ef = pd.DataFrame({"Returns":rets,"Volatility":vols})
    return ef.plot.line(x="Volatility",y="Returns",style=style)    
    
from scipy.optimize import minimize
def minimize_vol(target_return, er, cov):
    """
    target_return -> W
    """
    n = er.shape[0]
    init_guess = np.repeat(1/n,n)
    bounds = ((0.0,1.0),)*n   # the cooma is to create a tuple of tuples n times
    return_is_target = {
        'type':'eq',
        'args':(er,),
        'fun': lambda weights, er: target_return - portfolio_return(weights,er)
    }
    weights_sum_to_1 = {
        'type':'eq',
        'fun': lambda weights: np.sum(weights)-1 
    }
    results = minimize(portfolio_vol,init_guess,
                      args = (cov,),method="SLSQP",
                       options={'disp':False},
                       constraints=(return_is_target, weights_sum_to_1),
                       bounds=bounds
                      )    
    return results.x
    
    
def optimal_weights(n_points, er, cov):
    """
    -> list of weights to run the optimizer on to minimize the vol
    """
    target_rs = np.linspace(er.min(),er.max(), n_points)
    weights = [minimize_vol(target_return,er,cov) for target_return in target_rs]
    return weights

def gmv(cov):
    """
    Returns the weights of the Global Minimum Portfolio
    given the covariance matrix
    """
    n = cov.shape[0]
    return msr(0,np.repeat(1,n),cov)
def plot_ef(n_points, er, cov, show_cml=False,style=".-",riskfree_rate=0, show_ew=False, show_gmv=False):
    """
    Plots the N-asset efficient frontier
    """
    weights = optimal_weights(n_points,er,cov)
    rets = [portfolio_return(w,er) for w in weights]
    vols = [portfolio_vol(w, cov) for w in weights]                   
    ef = pd.DataFrame({"Returns":rets,"Volatility":vols})
    ax = ef.plot.line(x="Volatility",y="Returns",style=style)   
    if show_ew:
        n = er.shape[0]
        w_ew = np.repeat(1/n,n)
        r_ew = portfolio_return(w_ew,er)
        vol_ew = portfolio_vol(w_ew, cov)
        # display EW
        ax.plot([vol_ew],[r_ew],color="goldenrod",marker="o",markersize=12)
    if show_gmv:
        w_gmv = gmv(cov)
        r_gmv = portfolio_return(w_gmv,er)
        vol_gmv = portfolio_vol(w_gmv, cov)
        # display EW
        ax.plot([vol_gmv],[r_gmv],color="midnightblue",marker="o",markersize=10)
    if show_cml:
        ax.set_xlim(left=0)
        w_msr = msr(riskfree_rate,er,cov)
        r_msr = portfolio_return(w_msr,er)
        vol_msr = portfolio_vol(w_msr,cov)
        # Add CML
        cml_x = [0,vol_msr]
        cml_y = [riskfree_rate, r_msr]
        ax.plot(cml_x,cml_y,color="green",marker="o",linestyle="dashed",markersize=12,linewidth=2)
    return ax
    
    
def msr(riskfree_rate, er, cov):
    """
    Returns the weights of the portfolio that gives you the maximum sharpe ratio
    given the riskfree rate and expected returns and a covariance matrix
    Riskfree rate + ER + COV -> W
    """
    n = er.shape[0]
    init_guess = np.repeat(1/n,n)
    bounds = ((0.0,1.0),)*n   # the cooma is to create a tuple of tuples n times
    weights_sum_to_1 = {
        'type':'eq',
        'fun': lambda weights: np.sum(weights)-1 
    }
    def neg_sharpe_ratio(weights, riskfree_rate,er, cov):
        """
        Returns negative of sharpe ratio
        """
        r=portfolio_return(weights,er)
        vol =portfolio_vol(weights,cov)
        return -(r-riskfree_rate)/vol
        
    results = minimize(neg_sharpe_ratio, init_guess,
                      args = (riskfree_rate,er,cov,),method="SLSQP",
                       options={'disp':False},
                       constraints=(weights_sum_to_1),
                       bounds=bounds
                      )    
    return results.x    
    
    
    
    
    
    
    
    

    
    
    
    