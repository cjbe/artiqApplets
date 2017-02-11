#!/usr/bin/env python3.5
# From Artiq, modified to have optional line-style

import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph

from artiq.applets.simple import TitleApplet


class XYPlot(pyqtgraph.PlotWidget):
    def __init__(self, args):
        pyqtgraph.PlotWidget.__init__(self)
        self.args = args

    def data_changed(self, data, mods, title):
        def get_array_or_none(key):
            try:
                return np.array(data[key][1])
            except KeyError:
                return None

        y = get_array_or_none(self.args.y)
        if y is None:
            return
        x = get_array_or_none(self.args.x)
        if x is None:
            x = np.arange(len(y))
        error = get_array_or_none(self.args.error)
        fit = get_array_or_none(self.args.fit)

        if len(y) != len(x):
            return

        if error is not None and hasattr(error, "__len__"):
            if not len(error):
                error = None
            elif len(error) != len(y):
                return

        xi = np.argsort(x)

        if self.args.xscale:
            x /= self.args.xscale

        self.clear()
        symbol = "x" if not self.args.no_symbol else None
        pen = pyqtgraph.mkPen() if self.args.lines else None

        self.plot(x[xi], y[xi], pen=pen, symbol=symbol)
        self.setTitle(title)
        if error is not None:
            # See https://github.com/pyqtgraph/pyqtgraph/issues/211
            if hasattr(error, "__len__") and not isinstance(error, np.ndarray):
                error = np.array(error)
            errbars = pyqtgraph.ErrorBarItem(
                x=np.array(x), y=np.array(y), height=error)
            self.addItem(errbars)
        if fit is not None and len(x) == len(fit):
            self.plot(x[xi], fit[xi], pen=pyqtgraph.mkPen('g'))

        if self.args.xlabel:
            self.setLabel("bottom", self.args.xlabel)
        if self.args.ylabel:
            self.setLabel("left", self.args.ylabel)


def main():
    applet = TitleApplet(XYPlot)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("x", "X values", required=False)
    applet.add_dataset("error", "Error bars for each X value", required=False)
    applet.add_dataset("fit", "Fit values for each X value", required=False)

    applet.argparser.add_argument("--lines", action="store_true",
                                  help="Join data points with lines")
    applet.argparser.add_argument("--no-symbol", action="store_true",
                                  help="Do not use a data-point symbol")
    applet.argparser.add_argument("--xlabel", help="Label for x axis")
    applet.argparser.add_argument("--ylabel", help="Label for y axis")
    applet.argparser.add_argument("--xscale", type=float, 
                                  help="Scale x axis values")
    applet.run()

if __name__ == "__main__":
    main()
