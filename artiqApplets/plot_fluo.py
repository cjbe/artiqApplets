#!/usr/bin/env python3.5

import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph

from artiq.applets.simple import SimpleApplet


class XYPlot(pyqtgraph.PlotWidget):
    def __init__(self, args):
        pyqtgraph.PlotWidget.__init__(self)
        self.args = args

    def data_changed(self, data, mods):
        try:
            y = data[self.args.y][1]
        except KeyError:
            return
        x = data.get(self.args.x, (False, None))[1]
        #xScale = data.get(self.args.xScale, (False, 1))[1]
        #x /= xScale
        if x is None:
            x = np.arange(len(y))
        
        if not len(y) or len(y) != len(x):
            return

        self.clear()
        self.plot(x, y)



def main():
    applet = SimpleApplet(XYPlot)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("x", "1D array of point abscissas", required=False)
    #applet.add_dataset("xScale", "Scaling of x, x=x/xScale", required=False)
    applet.run()

if __name__ == "__main__":
    main()
