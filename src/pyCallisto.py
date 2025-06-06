import sys
sys.path.append('.')
import datetime as dt
#import pyfits
import astropy.io.fits as pyfits
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import cm
import os
import numpy as np
from matplotlib.dates import  DateFormatter
import sys
import matplotlib
import io
import pyCallistoUtils as utils		#local utility file
import copy
#from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
#from mpl_toolkits.axes_grid1.colorbar import colorbar

class pyCallisto:

	def __init__(self, HDUList):
		"""
		Create pyCallisto object from HDUList
		"""
		self.hdus = HDUList
		self.imageHdu = self.hdus[0]
		self.binTableHdu = self.hdus[1]
		self.imageHeader = self.imageHdu.header
		# get the dataMin amd maximum for colorbar
		self.dataMin = int(self.imageHdu.data.min())
		self.dataMax = int(self.imageHdu.data.max())
		self.dataMid = (self.dataMin + self.dataMax) / 2



	def __del__(self):
		#print("Clearing the memory by deleting the HDUlist object nothandled correctly by pyfits")
		self.hdus.close()



	@classmethod
	def fromFile(cls, infits):
		"""
		Create pyCallisto object from fits file on disc

		input arguments:
			infits: input fits file
		
		"""
		
		# checking number of HDUs
		if not utils.checkFitsCallisto(infits):
			#through an error here
			raise ValueError("No. of HDUs are wrong in input fits file, not a proper callisto file , cannot proceed")
			#print("No. of HDUs are wrong, not a proper callisto file ")
			#return -1
		
		#check bintable data accessible
		if not utils.checkBInTable(infits):
			#through an error here
			raise ValueError("Bintable data may be corrupted in input fits file, cannot proceed")
			#print "Problem with bintabledata"
			#return -1
		HDUList = pyfits.open(infits)
		return cls(HDUList)



	def spectrogram(self, option=3, xtick= 2, blevel=0, endPts= [False, False], figSize = (6,4), cmap=cm.jet, cBar=False, cBarOri='vertical', fontsize=14, vmax=0):

		"""
		Return a matplotlib.pyplot.plot object representing the plot of the input fits file.

		input arguments:
			xticks: frequency of xticks in mins (default =2 )
			blevel: background level (default = 0)
			figsize: a tuple representing size of image (default = (8,6))
			cmap: a matplotlib colormap object (default = cm.jet)
			cbar: to plot a colorbar or not (default = true)
			cBarOri: colorbar orientation (default = 'vertical')
			fontsize: fontsize used in plot (default = 14)

		"""
		#plot the fig 
		#fig, ax = plt.subplots(figsize=(7,7))
		fig, ax = plt.subplots(figsize = (figSize[0], figSize[1]))
		
		if option == 1:
			y, x = self.imageHdu.data.shape
			cax = ax.imshow(self.imageHdu.data, extent=[0, x, 0, y], aspect='auto', cmap=cmap, vmin=blevel, vmax=vmax)
			if cBar == True:
				ticks =list( np.linspace(blevel,self.dataMax, 10).astype('int')) #calculate 10 ticks positins 
				if cBarOri == 'horizontal':
					cBar = fig.colorbar(cax, ticks = ticks, orientation='horizontal')
				else:
					cBar = fig.colorbar(cax, ticks = ticks)
				cBar.set_label('Intensity', rotation= 90)		
		
			plt.xlabel('Row Count')
			plt.ylabel('Column Count')


		if option == 2:
			xStart = int(self.imageHeader['CRVAL1'])
			xStep = float(self.imageHeader['CDELT1'])  
			xLength = int(self.imageHeader['NAXIS1'])
			xEnd = xStart + xStep * xLength
			freqs = self.binTableHdu.data['frequency'][0]  # these are true frequencies
			cax = ax.imshow(self.imageHdu.data, extent=[xStart, xEnd, freqs[-1], freqs[0]], aspect='auto', cmap=cmap, vmin=blevel, vmax=vmax)
		
			if cBar == True:
				ticks =list( np.linspace(blevel,self.dataMax, 10).astype('int')) #calculate 10 ticks positins 
				if cBarOri == 'horizontal':
					cBar = fig.colorbar(cax, ticks = ticks, orientation='horizontal')
				else:
					cBar = fig.colorbar(cax, ticks = ticks)
				cBar.set_label('Intensity', rotation= 90)
			
			if endPts[1]:
				#set y minorticks for first and last frequency
				yLims = [freqs[-1], freqs[0]]
				#print(yLims)
				plt.yticks(list(plt.yticks()[0]) + yLims)
		
			plt.xlabel('Time (sec of day)')
			plt.ylabel('Frequency (MHz)')

		if option == 3:
			# get the start time and end time of observation
			startDate = utils.toDate(self.imageHeader['DATE-OBS'])
			startTime = utils.toTime(self.imageHeader['TIME-OBS'])
	
	
			startTime = dt.datetime.combine(startDate, startTime)  # make a datetime object
			endTime = utils.toTime(self.imageHeader['TIME-END'])
			endTime = dt.datetime.combine(startDate, endTime)
	
			# get the frequencies
			freqs = self.binTableHdu.data['frequency'][0]  # these are true frequencies
	
			# set the limits for plotting 
			xLims = [startTime, endTime]
			xLims = mdates.date2num(xLims)  # dates to numeric values
			yLims = [freqs[-2], freqs[1]]

	
	
			cax = ax.imshow(self.imageHdu.data, extent=[xLims[0], xLims[1],yLims[0], yLims[1]], aspect='auto', cmap=cmap, vmin=-10, vmax=vmax)
			if cBar == True:
				ticks =list( np.linspace(blevel,self.dataMax, 10).astype('int')) #calculate 10 ticks positins 
				if cBarOri == 'horizontal':
					cBar = fig.colorbar(cax, ticks = ticks, orientation='horizontal')
				else:
					cBar = fig.colorbar(cax, ticks = ticks)
				cBar.set_label('Intensity', rotation= 90)
		
			ax.xaxis_date()  # x axis has a date data
	
			ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(60), interval=xtick, tz=None))
			ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))

			#set ytick labels to be intigers only, in case we have a small frequency range, pyplot tends to show fraction 
			ax.get_yaxis().get_major_formatter().set_useOffset(False)
	
			if endPts[0]:
				#get the start time and end time ans set ticks at those position son x-axis using minor_locator
				total_sec = utils.tosec(endTime - startTime)
				ax.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=None, interval=total_sec, tz=None))
				ax.xaxis.set_minor_formatter(DateFormatter('%H:%M:%S'))
			fig.autofmt_xdate()
	
			if endPts[1]:
				#set y minorticks for first and last frequency
				plt.yticks(list(plt.yticks()[0]) + yLims)
				
			#ax.xaxis.set_minor_formatter(DateFormatter('%H:%M:%S'))
			plt.xlabel('Universal Time')
			plt.ylabel('Frequency (MHz)')

	
		#title = fitsfile + "\n" + imageHeader['DATE-OBS'] + "::" + imageHeader['TIME-OBS']
		title = self.imageHeader['CONTENT']
		plt.title(title)	
	#plt.show()
		return plt
		
    


	def appendTimeAxis(self, fits2):
		"""
		Take second radiohelliograph observation fits file and join two in time axis (x axis) and return new pyCallisto object.


		input arguments:
			fits2: path of a Second input fits file or pyCallisto object 
			
		"""


		#get imageData of first fits file
		imageData1 = self.imageHdu.data



		#get the image data of second fits file 
		#(which is the argument here, could be a string/path of fits file or pyCallisto object)

		#if argument is a string (representing path of fits file)
		if isinstance(fits2, str):
			#check if it is proper callisto file or not
			if not (utils.checkFitsCallisto(fits2)):
				raise Exception("Fits file is not proper callisto files")
				#print("Fits file is not proper callisto files")
				#return -1
			#get the data
			hdus = pyfits.open(fits2)
			imageHdu2 = hdus[0]
			binTableHdu2 = hdus[1]
			imageHeader2 = imageHdu2.header
			binHeader2 = binTableHdu2.header
			imageData2 = imageHdu2.data

		else:#if argument is a pyCallisto object
			
			imageHdu2 = fits2.hdus[0]
			binTableHdu2 = fits2.hdus[1]
			imageHeader2 = imageHdu2.header
			binHeader2 = binTableHdu2.header
			imageData2 = imageHdu2.data


		# check if both imagedats they have same y dimensions (frequency in out case)
		if not imageData1.shape[0] == imageData2.shape[0]:
			raise Exception("Frequency dimensions do not match, cannot concatinate files")
			#print("Frequency dimensions do not match, cannot concatinate files")
			#hdus.close()
			#return -1		

		# check the order of fits files in time axis, if not correct, flip it
		
		#get start time of first file
		startDate = utils.toDate(self.imageHeader['DATE-OBS'])
		startTime = utils.toTime(self.imageHeader['TIME-OBS'])
		startTime1 = dt.datetime.combine(startDate, startTime)  # make a datetime object

		#get start time of second
		startDate = utils.toDate(imageHeader2['DATE-OBS'])
		startTime = utils.toTime(imageHeader2['TIME-OBS'])
		startTime2 = dt.datetime.combine(startDate, startTime)  # make a datetime object

		#if input files in not proper  order in time swap them
		if not startTime1 < startTime2:
			imageHdu2, binTableHdu2, imageHeader2, binHeader2, imageData2, self.imageHdu, self.binTableHdu, self.imageHeader, self.binheader, imageData1 = self.imageHdu, self.binTableHdu, self.imageHeader, self.binheader, imageData1, imageHdu2, binTableHdu2, imageHeader2, binHeader2, imageData2 
			startTime1, startTime2 = startTime2, startTime1 
		
		# endTime of first file
		endDate = utils.toDate(self.imageHeader['DATE-END'])
		endTime = utils.toTime(self.imageHeader['TIME-END'])
		endTime1 = dt.datetime.combine(endDate, endTime)  # make a datetime object
	
		# check that two fits files are continuous in time axis
		td_sec = dt.timedelta(seconds=1)
		if startTime2 - endTime1 > td_sec:
			raise Exception("Fits  files are not continuous in time axis, cannot join them")
			#print("Fits  files are not continuous in time axis, cannot join them")
			#hdus.close()
			#return -1		
			#sys.exit(1)
	
		# check if both the files have same sampling /
		if not self.imageHeader['CDELT1'] == imageHeader2['CDELT1']:
			raise Exception("Two fits files do not have the same sampling in time axis, cannot join them")
			#print("Two fits files do not have the same sampling in time axis, cannot join them")
			#hdus.close()
			#return -1		
			#sys.exit(1)
	
		# join the numpy Array 
		imageData = np.concatenate((imageData1, imageData2), axis=1)
	
		# compose a new image header
		imageHeader = copy.deepcopy(self.imageHeader)
		imageHeader['NAXIS1'] = imageData.shape[1]
		imageHeader['DATE-END'] = imageHeader2['DATE-END']
		imageHeader['TIME-END'] = imageHeader2['TIME-END']
		imageHeader['DATAMIN'] = imageData.min()
		imageHeader['DATAMAX'] = imageData.max()
		imageHeader['COMMENT'] = "created on " + str(dt.datetime.now()) + " by joining fits files " # + str(self.infits) + " " + str(fits2)

		# create a primary hdu containing this image and header data
		imageHdu = pyfits.PrimaryHDU(imageData, header=imageHeader)
		newhdulist = pyfits.HDUList([imageHdu]) 
	
		# bintabledata
		xLength = int(self.imageHeader['NAXIS1']) + int(imageHeader2['NAXIS1']) 
		xLength = int(xLength)
		 
		rangeList = [x * 1.0 for x in range(xLength)]
		binTableDataTime = np.array([ rangeList ])
		bintableDataFreqs = list(self.binTableHdu.data[0][1].copy())
		bintableDataFreqs = np.array([bintableDataFreqs])
	
		# these two arrays needs to be two dimensional, though the content is one dimensional,
		# to be in sync with original data format, which is 1RX2C 
		#print binTableDataTime.shape
		#print bintableDataFreqs.shape
	
		# generalize the "format" 
		format1 = str(binTableDataTime.shape[1]) + "D8.3"
		format2 = str(bintableDataFreqs.shape[1]) + "D8.3"
		col1 = pyfits.Column(name='TIME', format=format1, array=binTableDataTime)
		col2 = pyfits.Column(name='FREQUENCY', format=format2, array=bintableDataFreqs)
		cols = pyfits.ColDefs(np.asarray([col1, col2]))
	
		# create bintable and  add it to hdulist
		tbhdu = pyfits.BinTableHDU.from_columns(cols)
		newhdulist.append(tbhdu)

		#return new pycallisto object
		return pyCallisto(newhdulist)


	def sliceTimeAxis(self, time1, time2):
		"""
		Make a slice of input radiohelliograph observation fits file along a time axis and return a new object
	
		input arguments:
			time1 (string): start of a slice, time in HH:MM:SSformat 			
			time2 (string): end of a slice, time in HH:MM:SS format
							
		Returns
			pyCallisto object
		"""

		# assuming that the input file has same start date and end date  (i.e. observed on the same day)
		# time1 and time 2 is in HH:MM:SS
		if not (len(time1.split(':')) == 3):
			raise Exception("Time format not proper, please provide time in HH:MM:SS format")
			#print "Time format not proper, please provide time in HH:MM:SS format"
			#return -1		
			#sys.exit(1)
	
		if not (len(time2.split(':')) == 3):
			raise Exception("Time format not proper, please provide time in HH:MM:SS format")
			#print "Time format not proper, please provide time in HH:MM:SS format"
			#return -1
			#sys.exit(1)
	
#		# open input fits file
#		hdus = pyfits.open(infits)
#		imageHdu = hdus[0]
#		binTableHdu = hdus[1]
#		imageHeader = imageHdu.header
#		imageData = imageHdu.data
	
		# check the dates
		startDate = utils.toDate(self.imageHeader['DATE-OBS'])
		endtDate = utils.toDate(self.imageHeader['DATE-END'])
		if not startDate == endtDate:
			raise Exception("startDate and enddate differ, right now we do not support this")
			#print "startDate and enddate differ, right now we do not support this"
			#hdus.close()
			#return -1
			#sys.exit(1)
		
		# get the times in datetime.date format for easy manipulation
		startTime = utils.toTime(self.imageHeader['TIME-OBS'])  # datetime.date object
		startTime = dt.datetime.combine(startDate, startTime)  # datetime.datetime object
		endTime = utils.toTime(self.imageHeader['TIME-END'])
		endTime = dt.datetime.combine(startDate, endTime)
	
		time1 = utils.toTime(time1)
		time1 = dt.datetime.combine(startDate, time1)
		time2 = utils.toTime(time2)
		time2 = dt.datetime.combine(startDate, time2)
	
		# check the "time constraints"
		if not (time1 < time2):
			time1, time2 = time2, time1
		if not (startTime < time1):
			#print("Time1 out of bound, can't slice!")
			print("Start time of input file : ", startTime)
			print("End time of input file : ", endTime)
			raise Exception("Time1 out of bound, can't slice!")
			#hdus.close()
			#return -1
			#sys.exit(1)
		if not (endTime > time2):
			#print("Time2 out of bound, can't slice!")
			print("Start time of input file : ", startTime)
			print("End time of input file : ", endTime)
			raise Exception("Time2 out of bound, can't slice!")
			#hdus.close()
			#return -1
			#sys.exit(1)
		
		# get the startPixel and endPixel in piselterms from input of time1 and time2 
		startPixel = time1 - startTime
		startPixel = utils.tosec(startPixel)  # in seconds
		startOffset = startPixel
		startPixel = int(startPixel / float(self.imageHeader['CDELT1']))
	
		endPixel = time2 - startTime
		endPixel = utils.tosec(endPixel)
		endPixel = int(endPixel / float(self.imageHeader['CDELT1']))
	
		# do the actual slicing
		imageData = copy.deepcopy(self.imageHdu.data)
		imageData = imageData[:, startPixel:endPixel]
	
		# update the imageHeader accordingly
		imageHeader = copy.deepcopy(self.imageHeader)
		imageHeader['NAXIS1'] = imageData.shape[1]
		imageHeader['TIME-OBS'] = str(time1.time())
		imageHeader['TIME-END'] = str(time2.time())
		imageHeader['DATAMIN'] = imageData.min()
		imageHeader['DATAMAX'] = imageData.max()
		imageHeader['CRVAL1'] = int(self.imageHeader['CRVAL1']) + startOffset 
	
		# create a primary hdu containing this image and header data
		imageHdu = pyfits.PrimaryHDU(imageData, header=imageHeader)
		newHduList = pyfits.HDUList([imageHdu])
	
		# create a new bintable and update it in data structure
		xLength = endPixel - startPixel 
		rangeList = [x * 1.0 for x in range(xLength)]
		binTableDataTime = np.array([ rangeList ])
		binTableDataFreqs = list(self.binTableHdu.data[0][1].copy())
		binTableDataFreqs = np.array([binTableDataFreqs]) 
	
		format1 = str(binTableDataTime.shape[1]) + "D8.3"
		format2 = str(binTableDataFreqs.shape[1]) + "D8.3" 
		col1 = pyfits.Column(name='TIME', format=format1, array=binTableDataTime)
		col2 = pyfits.Column(name='FREQUENCY', format=format2, array=binTableDataFreqs)
		cols = pyfits.ColDefs(np.asarray([col1, col2]))
		tbhdu = pyfits.BinTableHDU.from_columns(cols)
	
		# add it to new hdulist we have created
		newHduList.append(tbhdu)

		return pyCallisto(newHduList)
    


	def sliceFrequencyAxis(self, freq1, freq2):
		"""
		Make a slice of input radiohelliograph observation fits file along a frequency axis
	
		Input arguments:
			freq1 (int): start of a slice
			freq2 (int): end of a slice

		Returns:
			new pyCallisto object
		"""

		# convert  the input frequency from string to int
		freq1 = int(freq1)
		freq2 = int(freq2)
		#swap frequencies if not in proper orde
		if freq1 > freq2:
			freq1, freq2 = freq2, freq1


	#	# open input fits file
		hdus = self.hdus
		imageHdu = hdus[0]
		binTableHdu = hdus[1]
		imageHeader = imageHdu.header
		imageData = imageHdu.data
		bintblfreqdata = binTableHdu.data[0][1]

		# check the frequencies
		startFreq = int(bintblfreqdata[-1])
		endFreq = int(bintblfreqdata[0])

		#print("startFreq %d"%startFreq)
		#print("endFreq %d"%endFreq)
		
		
		
		if (freq1 < startFreq or freq1 > endFreq):
			#print("Frequency out of bound, cannot slice")
			print("Start Frequency of input file : ", startFreq)
			print("End Frequency of input file ", endFreq)
			raise Exception("Frequency out of bound, cannot slice")
			#hdus.close()
			#return -1
			#raise SystemExit, 0
			#sys.exit()
		
		if freq2 < startFreq or freq2 > endFreq :
			#print "Frequency out of bound, cannot slice"
			print("Start Frequency of input file : ", startFreq)
			print("End Frequency of input file ", endFreq)
			raise Exception("Frequency out of bound, cannot slice")
			#hdus.close()
			#return -1
			#raise SystemExit, 0
			#sys.exit()
	
		if  (freq2 - freq1 < 1):
			#print "Too thin slice demanded, cannot slice thinner than 1 unit"
			print("Start Frequency of input file : ", startFreq)
			print("End Frequency of input file ", endFreq)
			raise Exception("Too thin slice demanded, cannot slice thinner than 1 unit")
			#hdus.close()
			#return -1
			#raise SystemExit, 0
			#sys.exit()
	
		# update the bintabledata according to freq1 and freq2
		try:
			slicePt1 = np.argwhere((bintblfreqdata >= freq1) & (bintblfreqdata <= freq2))[0][0]
			slicePt2 = np.argwhere((bintblfreqdata > freq1) & (bintblfreqdata < freq2))[-1][-1]+1
					#+1 at slicept2 is needed to accomodate the slicing style of python to get the slice of exact size
			
	
		except:
			#print("frequency limits given are smaller than single channel, please increase it and retry")
			print("Start Frequency of input file : ", startFreq)
			print("End Frequency of input file : ", endFreq)
			raise Exception("frequency limits given are smaller than single channel, please increase it and retry")
			#hdus.close()
			#return -1	
		
	
		if (slicePt2 - slicePt1) < 1:
			#print "frequency limits given are smaller than single channel, please increase it and retry"
			print("Start Frequency of input file : ", startFreq)
			print("End Frequency of input file : ", endFreq)
			raise Exception("frequency limits given are smaller than single channel, please increase it and retry")
			#hdus.close()
			#return -1
			#raise SystemExit, 0
			#sys.exit(1)
		####
		binTableDataFreqs = bintblfreqdata[np.argwhere((bintblfreqdata >= freq1) & (bintblfreqdata <= freq2))]
		binTableDataFreqs = np.array([binTableDataFreqs])
		
		#print(type(binTableDataFreqs))
		#print(binTableDataFreqs.shape)
		#binTableDataFreqs = binTableDataFreqs[:,:-1,:]
		#print(binTableDataFreqs.shape)
		#binTableDataFreqs = binTableDataFreqs[:-1]	#removing the last entry, but we are sure of the mechanism here

		#################
		xLength = int(imageData.shape[1]) 
		rangeList = [x * 1.0 for x in range(xLength)]
		bintabledatatime = np.array([ rangeList ])
	
		#print("#########################")
		#print(bintabledatatime.shape)
		#print(binTableDataFreqs.shape)
		#print("#########################")
		
		format1 = str(bintabledatatime.shape[1]) + "D8.3"
		format2 = str(binTableDataFreqs.shape[1]) + "D8.3" 
		col1 = pyfits.Column(name='TIME', format=format1, array=bintabledatatime)
		col2 = pyfits.Column(name='FREQUENCY', format=format2, array=binTableDataFreqs)
		
		cols = pyfits.ColDefs(np.asarray([col1, col2]))
		tbhdu = pyfits.BinTableHDU.from_columns(cols)
	
		# update the imageHeader accordingly
		imageHeader = copy.deepcopy(self.imageHeader)
		imageData = copy.deepcopy(imageData)
		imageData = imageData[slicePt1:slicePt2, :]
		imageHeader['NAXIS2'] = imageData.shape[0]
		imageHeader['DATAMIN'] = imageData.min()
		imageHeader['DATAMAX'] = imageData.max()
		imageHeader['CRVAL2'] = imageData.shape[0]
		
		#print(slicePt1, slicePt2)
		#print(imageData.shape)
		
		# create a primary hdu containing this image and header data
		imageHdu = pyfits.PrimaryHDU(imageData, header=imageHeader)
		newHduList = pyfits.HDUList([imageHdu])
	 
		# add it to hdulist, and write hdulist  to  fits file
		newHduList.append(tbhdu)
	
		return pyCallisto(newHduList)







	def subtractBackground(self):
		"""
		Estimate and subtract background from a fits file
	
		returns a pyCallisto object		
		"""

		# open input fits file
		hdus = self.hdus
		imageHdu = hdus[0]
		binTableHdu = hdus[1]
		imageHeader = imageHdu.header
		imageData = imageHdu.data
	
		#print("size of the bintblfreqdata", type(binTableHdu.data), len(binTableHdu.data))
		bintblfreqdata = binTableHdu.data[0][1]
	
	
	
		#estimate background and subtract from original data
		medCol = np.median(imageData, axis=1, keepdims=1)
		imageData = copy.deepcopy(imageData)
		imageData = imageData - medCol


		#we need to update the header accordingly  ##############
		# compose a new image header
		imageHeader = copy.deepcopy(imageHeader)
		imageHeader['DATAMIN'] = imageData.min()
		imageHeader['DATAMAX'] = imageData.max()
	
	
		# create a primary hdu containing this updated image data
		imageHdu = pyfits.PrimaryHDU(imageData, header=imageHeader)
		newHduList = pyfits.HDUList([imageHdu])
	 
		# add the unchanged binTableHdu to hdulist
		newHduList.append(binTableHdu)

		return pyCallisto(newHduList)









	def meanLightCurve(self, plot=True, outImage ="timeseries.png", returnData=False, figSize = (8, 8), fontsize=14, grid = True):
		"""
		Create mean light curve by Collapse the 2D fits image along time axis.
		Eithers saves the image or returns the data
	
		Input arguments:
			plot (Boolean): plot it or not, Default True
			outImage(string): name of the image to be saved
			returnData (Boolean):  return data or not (default False)
	
		returns:if returnData is set to True 
				list of collapsed 1d array (1d numpy array), 
				 respective time in sec of a day(1d numpy array),
				 respective time in datetime.datetime object(1d list)			 
		"""
		# open input fits file
		hdus = self.hdus
		imageHdu = hdus[0]
		imageHeader = imageHdu.header
		imageData = imageHdu.data
		binTableHdu = hdus[1]
		bintblfreqdata = binTableHdu.data[0][1]
		
	
		# Sum the data along oth axis
		sumImage = np.sum(imageData, axis=0)
		#print("yshape")
		#print(imageData.shape[0])
		sumImage = sumImage / imageData.shape[0]		#divide by 200 to normalize
	
		startDate = utils.toDate(imageHeader['DATE-OBS'])
		startTime = utils.toTime(imageHeader['TIME-OBS'])
		startTime = dt.datetime.combine(startDate, startTime)  # make a datetime object
		endTime = utils.toTime(imageHeader['TIME-END'])
		endTime = dt.datetime.combine(startDate, endTime)
		timeDelta = dt.timedelta(days=0, hours=0, minutes=0, seconds=imageHeader['CDELT1'])

		def gettimeAxis(start, end, delta):
			curr = start
			while curr < end:
				yield curr
				curr += delta
	
		#timeAxis = [time for time in gettimeAxis(startTime, endTime, (endTime - startTime) / sumImage.shape[0])]
		timeAxis = [time for time in gettimeAxis(startTime, endTime, timeDelta) ]
		
		#0:00:00.249861
		#form delta from header information
		#
		
		#print(startTime)
		#print(endTime)
		#print ( ((endTime - startTime) / sumImage.shape[0]) )
		#print ( type((endTime - startTime) / sumImage.shape[0]) )
		#print (timeDelta)
		#print (type(timeDelta))
		#print(len(timeAxis))
		#print(timeAxis[0])
		#print(timeAxis[-1])
	
		if plot:
			#plt.clf()  #check back if this is needed
			#fig, ax = plt.subplots()
			fig, ax = plt.subplots(figsize = (figSize[0], figSize[1]))
			ax.plot_date(timeAxis, sumImage, 'b-', xdate=True)
			ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
			plt.xticks(rotation=45)
			plt.xlabel('Universal Time', fontsize=fontsize)
			plt.ylabel('Total count', fontsize=fontsize)
			#title = infits + "\n" + imageHeader['DATE-OBS'] + "::" + imageHeader['TIME-OBS']
			#title = self.imageHeader['CONTENT']
			
			plt.title("Mean light curve", fontsize=fontsize)
			if grid:
				plt.grid()
			#plt.show()
			plt.savefig(outImage)
		
		else:
			if returnData:	
				# generate numpy array of sec. of a day
				xStart = int(imageHeader['CRVAL1'])
				xStep = float(imageHeader['CDELT1'])  
				xLength = int(imageHeader['NAXIS1'])
				xEnd = xStart + (xStep * xLength)
				timeInSec = np.arange(xStart, xEnd, xStep)
		
				# compose data into a list
				data = [sumImage, timeInSec, timeAxis]
				#hdus.close()
				return data





	def meanSpectrum(self, plot=True, outImage ="frequency_series.png", returnData=False, fontsize = 14, grid = True):
		"""
		Create mean spectrum by collapsing the 2D fits image along frequency axis.
		Either plots image or returns data.
	
		INput arguments:
			plot (Boolean): plot or not ?, Default True
			outImage (String):  name of the png file to plot
			returnData (Boolean) : return data or not (Default False)
		
		returns : list of  collapsed 1d array (1d numpy array),
				respective frequency channels (1d numpy array)
		"""
	
		# open input fits file
		hdus = self.hdus
		imageHdu = hdus[0]
		binTableHdu = hdus[1]
		imageHeader = imageHdu.header
		imageData = imageHdu.data
		bintblfreqdata = binTableHdu.data[0][1]
	
		# Sum the data along oth axis
		sumImage = np.sum(imageData, axis=1)
		sumImage = sumImage / imageData.shape[1]		#divide by xsize to normalize
		 
		if plot:
			# fig, ax = plt.subplots()
			plt.clf()
			plt.plot(bintblfreqdata, sumImage, 'b-',)	#check why we need to add -1 here
			plt.axis([bintblfreqdata[-1], bintblfreqdata[0], sumImage.min(), sumImage.max()])
			plt.xlabel("Frequency (MHz)", fontsize=fontsize)
			plt.ylabel('Total count', fontsize=fontsize)
			#title = infits + "\n" + imageHeader['DATE-OBS'] + "::" + imageHeader['TIME-OBS'] + " To " + imageHeader['DATE-END'] + "::" + imageHeader['TIME-END']
			#title = self.imageHeader['CONTENT']
			plt.title("Mean Spectrum", fontsize=fontsize)
			if grid:
				plt.grid()
			plt.savefig(outImage)
			#hdus.close()
		else:
			if returnData: 
				# compose data into a list
				data = [sumImage, bintblfreqdata]
				hdus.close()
				return data





	def printFrequencies(self):
		"""
		Print the list of frequencies.
		"""
		# open input fits file
		hdus = self.hdus
		imageHdu = hdus[0]
		binTableHdu = hdus[1]
		imageHeader = imageHdu.header
		imageData = imageHdu.data
		bintblfreqdata = binTableHdu.data[0][1]
		
		print(np.array2string(binTableHdu.data[0][1]))
	





##############################################################################
#lightcurve: time vs amplitude for given frequency / band
#spectrum: frequency vs amplitude for given time

	def lightCurve(self, frequency, plot=True, outImage ="Lightcurve.png", returnData=False, figSize = (8, 8), fontsize=14, grid =True):
		"""
		Plot the lightcurve for given frequency, i.e. time vs amplitude, or return the data
	
		Input arguments:
			frequency: frequency to plot lightcurve
			plot (Boolean): plot it or not (Default = True)
			outImage: Name of the image to save, default is "Lightcurve.png"
			returnData (Boolean) : return the data or not (default = False)
			figsize: size of the fig (default = (8, 8))
			fontsize: fontsize of the used in plots (default =14)
			grid: to plot agrid or not (default = True)
		returns:if returnData is set to True 
#				return a tuple of (timeAxis, lightCurve)
				where 
					timeAxis is array of python dataetime object 
					lightCurve is numpy array
		"""
		
		# open input fits file
		hdus = self.hdus
		imageHdu = hdus[0]
		binTableHdu = hdus[1]
		imageHeader = imageHdu.header
		imageData = imageHdu.data
		bintblfreqdata = binTableHdu.data[0][1]
		bintblfreqdata = binTableHdu.data[0][1]

		#check input frequency
		startFreq = int(bintblfreqdata[-1])
		endFreq = int(bintblfreqdata[0])
		if(frequency < startFreq or frequency > endFreq):
			raise Exception("Input frequency is out of limit for this data, aborting the operation")
		
		
		
		#get the nearest value in the bintable to the user input frequency
		minDiff = (np.abs(bintblfreqdata -frequency)).min()
		idx = (np.abs(bintblfreqdata -frequency)).argmin()
		nearestFrequency = bintblfreqdata[idx]
		#print("input frequency %d"%frequency)
		#print("nearest frequency %g"%nearestFrequency)
		#print("difference is  %g"%minDiff)
#		
		#give warning if the difference between input frequency and the nearest frequency is greater than 5
		if minDiff > 5:
			print("Please note that the difference between demanded frequency and the nearest one in data is %g"%minDiff)


		#get the corresponding row from imageData
		lightCurve = imageData[idx,:]
		#print(type(lightCurve))
		
		#get startdate-time and enddate-time
		startDate = utils.toDate(imageHeader['DATE-OBS'])
		startTime = utils.toTime(imageHeader['TIME-OBS'])
		startTime = dt.datetime.combine(startDate, startTime)  # make a datetime object
		endTime = utils.toTime(imageHeader['TIME-END'])
		endTime = dt.datetime.combine(startDate, endTime)

		def gettimeAxis(start, end, delta):
			curr = start
			while curr < end:
				yield curr
				curr += delta
	
		timeAxis = [time for time in gettimeAxis(startTime, endTime, (endTime - startTime) / lightCurve.shape[0])]
	
		if plot:
			plt.clf()
			#fig, ax = plt.subplots()
			fig, ax = plt.subplots(figsize = (figSize[0], figSize[1]))
			ax.plot_date(timeAxis, lightCurve, 'b-', xdate=True)
			ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
			plt.xticks(rotation=45)
			
			plt.xlabel('Universal Time', fontsize=fontsize)
			plt.ylabel('Amplitude', fontsize=fontsize)
			#title = infits + "\n" + imageHeader['DATE-OBS'] + "::" + imageHeader['TIME-OBS']
			#title = self.imageHeader['CONTENT'] 
			title = "Light curve - "+str(round(nearestFrequency, 2))+" MHz"
			plt.title(title, fontsize=fontsize)
			if grid:
				plt.grid()
			#plt.show()
			plt.savefig(outImage)
			#plt.clf()
		else:
			if returnData:	
				return (timeAxis, lightCurve)




	def spectrum(self, inDate, inTime, binning = 2, binningMethod= 'avg', plot=True, outImage ="singletimespectrum.png", returnData=False, figSize = (8, 6), fontsize=14, grid=True):
		"""
		Plot the spectrum for a given time, i.e. amplitude at all frequencies at given time
	
		Input arguments:
			indate :date to plot spectrum of, 
					should be a python datetime object or 
					string of format 'YYYY/MM/DD'
			intime : time to plot spectrum of, 
					should be a python datetime.time object or 
					string of format 'HH:MM:SS'
			binning: pixel-level binning while selecting a row (default = 2)
				caution, only advanced users should alter this parameter
			binnigmethod : either of avg, sum, med (default = 'avg')
			plot (Boolean) : plot it or not, Default True
			outimage : Name of the image to save, default is "singletimespectrum.png"
			returndata (Boolean) :   default False
			figsize: size of the fig (default = (8, 8))
			fontsize: fontsize of the used in plots (default =14)
			grid: to plot agrid or not (default = True)
	
		returns:if returndata is set to True 
				return a tuple of (bintblfreqdata, spectrum)
				where 
					bintblfreqdata :  list of frequencies
					spectrum :  intensity count at these respective ffrequencies

		"""
		
		# open input fits file
		hdus = self.hdus
		imageHdu = hdus[0]
		binTableHdu = hdus[1]
		imageHeader = imageHdu.header
		imageData = imageHdu.data
		bintblfreqdata = binTableHdu.data[0][1]
		bintblfreqdata = binTableHdu.data[0][1]


		#get startdate-time and enddate-time of the file
		startDate = utils.toDate(imageHeader['DATE-OBS'])
		startTime = utils.toTime(imageHeader['TIME-OBS'])
		startTime = dt.datetime.combine(startDate, startTime)  # make a datetime object
		endTime = utils.toTime(imageHeader['TIME-END'])
		endTime = dt.datetime.combine(startDate, endTime)
		#check the format of in date and intime


		if(isinstance(inDate, dt.date) and isinstance(inTime, dt.time)):
			inDateTime = dt.datetime.combine(inDate, inTime)
		else:
			if(isinstance(inDate, str) and isinstance(inTime, str)):
				if(len(inDate.split('/')) == 3):
					#year, month, day = indate.split('/')
					inDate = utils.toDate(inDate)
				else:
					raise Exception("Date string not in proper format")
				
				if(len(inTime.split(':')) == 3):
					#hr, mint, sec = intime.split(':')
					inTime = utils.toTime(inTime)
				else:
					raise Exception("Time string not in proper format")
				inDateTime = dt.datetime.combine(inDate, inTime)
			else:
				raise Exception("Date and/or time not in proper format")

		
			#check input time
		if(inDateTime < startTime or inDateTime > endTime):
			print("Provided datetime is "+str(inDateTime))
			print("Start datetime for this file is "+str(startTime))
			print("End datetime for this file is"+str(endTime))
			raise Exception("Input time is out of limit for this data, aborting the operation")
			
			
		#get the columnnumber of given datetime in a imageData
		def gettimeaxis(start, end, delta):
			curr = start
			while curr < end:
				yield curr
				curr += delta
	
		timeAxis = [time for time in gettimeaxis(startTime, endTime, (endTime - startTime) / imageData.shape[1])]
		#print(len(timeAxis))
		#print(timeAxis.index(inDateTime))
		#print(timeAxis[timeAxis.index(inDateTime)])
		timeIndex = timeAxis.index(inDateTime) 
		spectrum = imageData[:,timeIndex-binning:timeIndex+binning+1]
		
		
		#convert to numpy array
		#spectrum = np.array(spectrum)
		#print(spectrum)
		
		#print(spectrum.shape)
		if binningMethod == 'med':
			spectrum = np.median(spectrum, axis=1) 
		if binningMethod == 'sum':
			spectrum = spectrum.sum(axis=1) 
		if binningMethod == 'avg':
			spectrum = np.average(spectrum, axis=1) 
			#spectrum = spectrum / (bining*2+1)
		#print(spectrum.shape)
		
		if plot:
			plt.clf()
			#fig, ax = plt.subplots(figsize=(7, 6))
			fig, ax = plt.subplots(figsize = (figSize[0], figSize[1]))
			ax.plot_date(bintblfreqdata, spectrum, 'b-', xdate=True)
			ticks =list( np.linspace(bintblfreqdata[-1], bintblfreqdata[0], 20).astype('int')) #calculate 200 ticks positins 
			plt.xticks(ticks, ticks, rotation= 45)
			#ax.xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))
			plt.xlabel('Frequency (MHz)', fontsize= fontsize)
			plt.ylabel('Amplitude', fontsize= fontsize)
			#title = infits + "\n" + imageHeader['DATE-OBS'] + "::" + imageHeader['TIME-OBS']
			#title = self.imageHeader['CONTENT']
			title = "Spectrum - "+str(inDateTime)
			plt.title(title)
			if grid:
				plt.grid()
			#plt.show()
			plt.savefig(outImage)
			#plt.clf()
			
			#print(bintblfreqdata.shape)
			#print(bintblfreqdata)
		else:	
			if returnData:	
				return (bintblfreqdata, spectrum)



	def universalPlot(self, plotName = "universal_plot_with_add_processing.png", title='Universal Plot',returnPlot=False,xtick=3,ytick=3, endPts= [False, False], blevel=0,figSize=(10,8), cmap=cm.jet, labelfontsize=10, titlefontsize=14, cBar=True, cBarOri='horizontal'):
		"""
		plot universal plot


		input arguments:
			plotName: name of the image to be saved
			title: title of plot
			returnPlot: to return matplotlib plot object or not (defayult = False)
			xtick: frequency of xticks in minutes (default = 3)
			ytick: frequency of yticks in minutes (default = 3)
			endPts:	plot endpoints on x and y axis irrespective of ticks (fefault= (False, false))
			blevel: background level (default = 0)
			figSize:  tuple representing size of image (default = (8,6))
			cmap: a matplotlib colormap object (default = cm.jet)
			labelfontsize: fontsize used in plot for labels (default = 10)
			titlefontsize: fontsize used in plot for title (default = 14)
			cBar: to plot a colorbar or not (default = true)
			cBarOri: colorbar orientation (default = 'vertical')
		"""

		#create global plot object with subplot
		fig=plt.figure(figsize = (figSize[0], figSize[1]))
		

		#plot the spectrogram in the one subplot
		ax1=plt.subplot2grid(shape=(8,8),loc=(0,0),rowspan=5,colspan=5)
#		ax2 = plt.subplot2grid(shape=(9,8),loc=(6,0),rowspan=3,colspan=5, sharex=ax1)
#		ax3 = plt.subplot2grid(shape=(9,8),loc=(1,5),rowspan=5,colspan=3, sharey=ax1)
		
		# get the start time and end time of observation
		startDate = utils.toDate(self.imageHeader['DATE-OBS'])
		startTime = utils.toTime(self.imageHeader['TIME-OBS'])


		startTime = dt.datetime.combine(startDate, startTime)  # make a datetime object
		endTime = utils.toTime(self.imageHeader['TIME-END'])
		endTime = dt.datetime.combine(startDate, endTime)

		# get the frequencies
		freqs = self.binTableHdu.data['frequency'][0]  # these are true frequencies

		# set the limits for plotting 
		xLims = [startTime, endTime]
		xLims = mdates.date2num(xLims)  # dates to numeric values
		yLims = [freqs[-1], freqs[0]]


		im1 = ax1.imshow(self.imageHdu.data, extent=[xLims[0], xLims[1], yLims[0], yLims[1]], aspect='auto', cmap=cmap, vmin=blevel)
#		ax1_divider = make_axes_locatable(ax1)
#		cax1 = ax1_divider.append_axes("top", size="7%", pad="2%")
#		cb1 = colorbar(im1, cax=cax1, orientation="horizontal")
#		cax1.xaxis.set_ticks_position("top")
#		
#		if cBar == True:
#			ticks =list( np.linspace(blevel,self.dataMax, 10).astype('int')) #calculate 10 ticks positins 
#			if cBarOri == 'horizontal':
#				cBar = fig.colorbar(cax, ticks = ticks, orientation='horizontal', )
#			else:
#				cBar = fig.colorbar(cax, ticks = ticks)
#			cBar.set_label('Intensity', rotation= 90)

		#do not plot x ticks as it will share with the bottom subplot
		#ax1.xaxis_date()  # x axis has a date data
		#ax1.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(60), interval=xtick, tz=None))
		#ax1.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
		#ax1.tick_params(axis='x',size=2)

		#set ytick labels to be intigers only, in case we have a small frequency range, pyplot tends to show fraction 
		ax1.get_yaxis().get_major_formatter().set_useOffset(False)
		plt.minorticks_on()
		
		
		if endPts[0]:
			#get the start time and end time ans set ticks at those position son x-axis using minor_locator
			total_sec = utils.tosec(endTime - startTime)
			ax1.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=None, interval=total_sec, tz=None))
			ax1.xaxis.set_minor_formatter(DateFormatter('%H:%M:%S'))
		fig.autofmt_xdate()

		if endPts[1]:
			#set y minorticks for first and last frequency
			plt.yticks(list(plt.yticks()[0]) + yLims)
		
		#plt.xlabel('Universal Time')
		plt.ylabel('Frequency (MHz)',fontsize=labelfontsize)
		
		#title = fitsfile + "\n" + imageHeader['DATE-OBS'] + "::" + imageHeader['TIME-OBS']
		#ax1.axes.get_xaxis().set_visible(False) 
		
		ax1.tick_params(direction='in', axis='both', which='both')
		ax1.yaxis.set_ticks_position('both')
		ax1.xaxis.set_ticks_position('both')
		ax1.tick_params(labelbottom=False)
		
		
		#ax1.set_aspect('auto')
		
		#title = self.imageHeader['CONTENT']
		#plt.title(title)	
		#plt.show()
		#return plt


#		ax1_1 = plt.subplot2grid(shape=(9,8),loc=(0,0),rowspan=1,colspan=5, sharex=ax1)
#		im1 = ax1_1.imshow(self.imageHdu.data, extent=[xLims[0], xLims[1], yLims[0], yLims[1]], aspect='auto', cmap=cmap, vmin=blevel)
#		ticks =list( np.linspace(blevel,self.dataMax, 10).astype('int')) #calculate 10 ticks positins 
#		im1.set_visible(False)
#		cBar = fig.colorbar(im1, ticks = ticks, orientation='horizontal', )


		ax2 = plt.subplot2grid(shape=(8,8),loc=(5,0),rowspan=3,colspan=5, sharex=ax1)
		#ax2 = plt.subplot2grid(shape=(8,8),loc=(5,0),rowspan=3,colspan=5, sharex=ax1)
#		ax2 = plt.subplot2grid(shape=(8,8),loc=(5,0),rowspan=3,colspan=5)
		#ax3 = plt.subplot(313, sharex=ax1, sharey=ax1)
		
		#use meanlightcurve to get the lightcurve data
		data = self.meanLightCurve(plot=False, returnData=True) 
		sumImage, timeInSec, timeAxis = data
		#print(type(data))
		#print(len(data))
		#print()
		plt.minorticks_on()
		plt.xticks(rotation=45)
		ax2.plot(timeAxis, sumImage, 'k')
		ax2.tick_params(direction='in', axis='both', which='both')
		ax2.yaxis.set_ticks_position('both')
		ax2.xaxis.set_ticks_position('both')
		ax2.margins(0.0)
		ax2.set_xlabel('Universal Time')




		#define ax3
		ax3 = plt.subplot2grid(shape=(8,8),loc=(0,5),rowspan=5,colspan=3, sharey=ax1)
		#ax3 = plt.subplot2grid(shape=(8,8),loc=(0,5),rowspan=4,colspan=3, sharey=ax1)
		#ax3 = plt.subplot2grid(shape=(8,8),loc=(0,5),rowspan=5,colspan=3)
		#use meanspectrum to get spectrum data
		data = self.meanSpectrum(plot=False, returnData=True)
		sumImage, bintblfreqdata = data
		#use spectrum data to plot spectrum in third subplot
		ax3.plot(sumImage, bintblfreqdata, 'k')
		#ax3.yaxis.tick_right()
		plt.minorticks_on()
		ax3.tick_params(direction='in', axis='both', which='both')
		ax3.yaxis.set_ticks_position('both')
		ax3.xaxis.set_ticks_position('both')
		#ax3.tick_params(direction='in', axis='both', which='both')
		ax3.tick_params(labelleft=False)
		ax3.tick_params(labelright=True)
		ax3.invert_xaxis()
		plt.xticks(rotation=45)
		ax3.margins(0.0)
		#plt.tight_layout()


		plt.suptitle(title, fontsize = titlefontsize + 4)
		fig.subplots_adjust(right=0.8)
		cbar_ax = fig.add_axes([0.85, 0.15, 0.03, 0.7])
		fig.colorbar(im1, cax=cbar_ax)
		plt.savefig(plotName)
        
"""		
    def plotSpectrogramWithGOES(self, tstart, tend, satellite_number=16, xtick=2, blevel=0, figSize=(10, 8), cmap=cm.jet, fontsize=14, save_path="spectrogram_with_goes.png"):
        
        Plot the spectrogram and superimpose the GOES X-ray flux data.

        Parameters:
            tstart (str): Start time for GOES data in "YYYY-MM-DD HH:MM" format.
            tend (str): End time for GOES data in "YYYY-MM-DD HH:MM" format.
            satellite_number (int): GOES satellite number (default = 16).
            xtick (int): Frequency of x-axis ticks in minutes.
            blevel (int): Background level for spectrogram.
            figSize (tuple): Size of the figure (width, height).
            cmap: Colormap for the spectrogram.
            fontsize (int): Font size for labels and titles.
            save_path (str): Path to save the output plot.

        Returns:
            None: Saves the plot to the specified path.
        
        import matplotlib.dates as mdates
        from sunpy.net import Fido
        from sunpy.net import attrs as a
        from sunpy import timeseries as ts
        from matplotlib.dates import DateFormatter

        # Plot the spectrogram
        fig, ax1 = plt.subplots(figsize=figSize)
        startDate = utils.toDate(self.imageHeader['DATE-OBS'])
        startTime = utils.toTime(self.imageHeader['TIME-OBS'])
        startTime = dt.datetime.combine(startDate, startTime)
        endTime = utils.toTime(self.imageHeader['TIME-END'])
        endTime = dt.datetime.combine(startDate, endTime)
        freqs = self.binTableHdu.data['frequency'][0]
        xLims = [startTime, endTime]
        xLims = mdates.date2num(xLims)
        yLims = [freqs[-1], freqs[0]]

        cax = ax1.imshow(self.imageHdu.data, extent=[xLims[0], xLims[1], yLims[0], yLims[1]],
                     aspect='auto', cmap=cmap, vmin=blevel)

        ax1.xaxis_date()
        ax1.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(60), interval=xtick))
        ax1.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        ax1.set_xlabel('Universal Time', fontsize=fontsize)
        ax1.set_ylabel('Frequency (MHz)', fontsize=fontsize)
        ax1.tick_params(axis='both', labelsize=fontsize)
        plt.colorbar(cax, ax=ax1, orientation='vertical', label='Intensity')

        # Fetch and overlay GOES X-ray flux
        result = Fido.search(a.Time(tstart, tend), a.Instrument("XRS"), a.goes.SatelliteNumber(satellite_number))
        files = Fido.fetch(result)
        goes_data = ts.TimeSeries(files, concatenate=True)
        goes_df = goes_data.to_dataframe()
        goes_df = goes_df[(goes_df["xrsa_quality"] == 0) & (goes_df["xrsb_quality"] == 0)]

        ax2 = ax1.twinx()  # Create a secondary y-axis for GOES data
        ax2.plot(goes_df.index, goes_df["xrsb"], 'r-', label="GOES X-ray Flux")
        ax2.set_ylabel('X-ray Flux (W/m²)', fontsize=fontsize, color='red')
        ax2.tick_params(axis='y', labelcolor='red', labelsize=fontsize)
        ax2.legend(loc='upper right')

        # Title and save the plot
        plt.title("Spectrogram with GOES X-ray Flux Overlay", fontsize=fontsize + 2)
        plt.savefig(save_path)
        plt.close()
		
"""        
		
		
