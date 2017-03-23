#!/usr/bin/env python3.5
import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph as pg

from artiq.applets.simple import SimpleApplet


class CorrelationPlot(pg.PlotWidget):
    def __init__(self, args):
        super().__init__(self)
        self.args = args
        self.setWindowTitle("Correlations")

        datasets = ["p00", "p01", "p10", "p11"]
        self.datasets = ["{}{}".format(args.prefix, d) for d in datasets]

    def _set_full_plot(self, x, yy):
        self.clear()

        for i, y in enumerate(yy):
            self.plot(x, y, pen=None, symbolPen=(i, len(yy)), symbol="x")
        self.addLegend()

    def _set_partial_plot(self, x, yy):
        self.clear()

        # add together 01 and 10 for odd parity
        odd = yy[0b01] + yy[0b10]
        # take even as 11
        even = yy[0b11]

        self.plot(x, odd, pen=None, symbol="x")
        self.plot(x, even, pen=None, symbol="o")
        self.addLegend()

    def data_changed(self, data, mods):
        try:
            yy = []
            for name in self.datasets:
                yy.append(data[name][1])
        except KeyError:
            return

        x = data.get(self.args.x, (False, None))[1]
        if x is None:
            x = np.arange(len(yy[0]))

        if self.args.all:
            self._set_full_plot(x, yy)
        else:
            self._set_partial_plot(x, yy)


def main():
    applet = SimpleApplet(CorrelationPlot)
    applet.argparser.add_argument("--all", "-a",
                                  help="Plot all correlations",
                                  action='store_true')
    applet.argparser.add_argument("--prefix", "-p",
                                  help="Optional dataset prefix", default='')
    applet.add_dataset("x", "X values", required=False)
    applet.run()


if __name__ == "__main__":
    main()

