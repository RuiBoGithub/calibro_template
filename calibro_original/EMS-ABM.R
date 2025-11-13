#This file contain the commands to run the exmaple "simplest" within R

library(calibro)                          #loads Calibro
CE = calEnv$new(name = 'simplest')        #creates a new calibration environment
CE$add.ds(name = 'data1', Y.star = 'obs.csv', TT = 'calib_sampling-EMS-ABM-u.csv', Y = 'df_q1_q3_q4_hvac_filtered.csv')  #adds a calibration data-et
CE$rd = 'pca'	#perform PCA
CE$sa = 'sobolSmthSpl'	#perform sensitivity analysis with sobolSmthSpl
CE$ret = list(mthd = 'ng.screening')	#perform factor retention with ng.screening
CE$mdls = 'gpr.ng.sePar01_whitePar01'	#build an emulator of the given type
CE$train = list(type = 'training', alg = 'amoeba')	#train emulator
CE$cals = 'cal.gpr.ng'	#build calibrator
CE$cal.mcmc = list(alg = 'amg')	#calibrate with Adaptive Metropolis within Gibbs
CE$cal.res()	#returns calibration results
CE$genReport(type = 'pdf', out = c('dss', 'cal'))	#generates json report
