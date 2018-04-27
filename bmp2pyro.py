#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

'''
@author: Nandor Toth
'''

import os
import sys
import getopt
import time
import logging
from PIL import Image
    
class BmpToPyro():
    FEED_RATE_BLACK = 400
    FEED_RATE_WHITE = 4000
    FEED_RATE_WHITE_PLUS = 6000
    RES_X = 0.1 # mm
    RES_Y = 0.1 # mm    
    
    def __init__(self, inFileName='', outFileName=''):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.img = Image.open(inFileName)  
        self.pix = self.img.load()
        self.sizeX, self.sizeY = self.img.size
        self.aspectRatio = self.sizeX / self.sizeY
        self.stepX = 0.1 # mm
        self.stepY = 0.1 # mm
        self.dimX = self.sizeX * self.stepX # mm
        self.dimY = int(100 * self.dimX / self.aspectRatio) / 100.0
        self.scaleX = self.dimX / self.sizeX
        self.scaleX = int(100 * self.scaleX) / 100.0
        self.scaleY = self.dimY / self.sizeY
        self.scaleY = int(100 * self.scaleY) / 100.0
                
        self.gcodeLines = []
        
        self.gcodeOutputFile = outFileName
        try:
            os.remove(self.gcodeOutputFile)
        except OSError:
            pass               
        
    def print_pixels_RGB(self):
        for x in range(0, self.sizeX):
            for y in range(0, self.sizeY):
                    print(self.pix[x,y])
        
    def print_feed_rates(self):
        for x in range(0, self.sizeX):
            for y in range(0, self.sizeY):
                    print(self.get_feed_rate_at_pixel(x, y))

    def print_gcode(self, xy, absPos, feedRate=None):        
        if feedRate is None:
            gcode = 'G01 %s%s' % (xy, absPos)
        else:
            gcode = 'G01 %s%s F%s' % (xy, absPos, feedRate)
        self.logger.debug(gcode)
        
        self.gcodeLines.append(gcode)

    def update_progressbar(self, percent):
        length = 25
        actual = int(percent * length)
        percentStr =  '%s%%' % (int(percent * 100))  
        print('\r[' + '|'*actual + ' '*(length-actual) + '] ' + percentStr, end='', flush=True)
        if percent == 1:
            print()
            
    def print_gcode_line(self):
        lastFeedRate = 0
        for y in range(0, self.sizeY):
            yAbsPos = int(y * self.scaleY * 100) / 100.0
            self.print_gcode('Y', yAbsPos)
            for x in range(0, self.sizeX):            
                xAbsPos = int(x * self.scaleX * 100) / 100.0
                feedRate = self.get_feed_rate_at_pixel(x, y)                
                if lastFeedRate != feedRate:
                    lastFeedRate = feedRate
                    self.print_gcode('X', xAbsPos, feedRate)
            self.print_gcode('X', xAbsPos, feedRate)
            self.print_gcode('X', 0, self.FEED_RATE_WHITE_PLUS)
            self.update_progressbar(y / (self.sizeY-1))
        
    def get_feed_rate_at_pixel(self, x, y):
        dot = self.pix[x,y] 
        gs = int((dot[0] + dot[1] + dot[2]) / 3) # greyscale, check only R channel
        if gs == 255:
            feed = self.FEED_RATE_WHITE_PLUS
        else:
            feed = self.mapVal(gs, 0, 255, self.FEED_RATE_BLACK, self.FEED_RATE_WHITE) 
        return feed
        
    def mapVal(self, x, in_min, in_max, out_min, out_max):
        ret = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
        ret = int(ret * 1) / 1.0
        return ret
    
    def writeToFile(self):
        with open(self.gcodeOutputFile, 'a') as f:
            for line in self.gcodeLines:
                f.write(line + '\n')
            
def main(argv):
    inputFile = ''
    outputFile = ''
    helpMsg = 'bmp2pyro.py -i <inputFile.bmp> -o <outputFile.nc>'    
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["iFile=","oFile="])
    except getopt.GetoptError:
        print(helpMsg)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(helpMsg)
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputFile = arg
        elif opt in ("-o", "--ofile"):
            outputFile = arg
    
    if inputFile == '':
        print('Please specify input file name!')
        print(helpMsg)
        sys.exit(2)
    if outputFile == '':
        outputFile = inputFile.split('.')[0] + '.nc'
        
    startedAt = time.time()
    b2f = BmpToPyro(inputFile, outputFile)
    # b2f.print_pixels_RGB()
    # b2f.print_feed_rates()    
    b2f.print_gcode_line()
    b2f.writeToFile()
    print('%s lines of gcode were written in %.2f secs' % (len(b2f.gcodeLines), (time.time() - startedAt)))
    print('Ready!')

if __name__ == '__main__':
    logging.basicConfig(level = logging.ERROR)
    main(sys.argv[1:])
