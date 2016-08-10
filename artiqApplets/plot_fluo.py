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
        x = np.arange(len(y))

        self.clear()
        self.plot(x, y)



def main():
    applet = SimpleApplet(XYPlot)
    applet.add_dataset("y", "Y values")
    applet.run()

if __name__ == "__main__":
    main()
