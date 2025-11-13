
setwd("/Users/rui.bo/Desktop/Working/1-phd_mainworks/Y3/calibro/exp_2/output")

library(calibro)

CE <- calEnv$new(name = 'simplest')

CE$add.ds(
    name = 'data1',
    Y.star = '/Users/rui.bo/Desktop/Working/1-phd_mainworks/Y3/calibro/exp_2/data/obs.csv',
    TT     = '/Users/rui.bo/Desktop/Working/1-phd_mainworks/Y3/calibro/exp_2/data/TT.csv',
    Y      = '/Users/rui.bo/Desktop/Working/1-phd_mainworks/Y3/calibro/exp_2/data/Y.csv'
)

CE$rd = 'pca'
CE$sa = 'sobolSmthSpl'
CE$ret = list(mthd = 'ng.screening')
CE$mdls = 'gpr.ng.sePar01_whitePar01'
CE$train = list(type = 'training', alg = 'amoeba')
CE$cals = 'cal.gpr.ng'
CE$cal.mcmc = list(alg = 'amg')

CE$cal.res()

# IMPORTANT: no 'path' argument allowed
CE$genReport(
    type = 'pdf',
    out  = c('dss','cal')
)
