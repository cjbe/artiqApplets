#!/usr/bin/env python3.5

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
import pyqtgraph
from scipy.stats import binom

from artiq.applets.simple import SimpleApplet


def _threshold_counts(counts, threshold):
    y = []
    y_upper_err = []
    y_lower_err = []
    for countVec in counts:
        p = sum([x >= threshold for x in countVec]) / len(countVec)
        y.append(p)
        kci = binom.interval(0.68, len(countVec), p) 
        y_lower_err.append( p - kci[0]/len(countVec) )
        y_upper_err.append( kci[1]/len(countVec) - p )
    return y, y_upper_err, y_lower_err

def _histogram_counts(counts, bins):
    hists = []
    for countVec in counts:
        hist, bins = np.histogram(countVec, bins=bins)
        hists.append(hist)
    return hists


class XYHistPlot(QtWidgets.QSplitter):
    def __init__(self, args):
        QtWidgets.QSplitter.__init__(self)
        self.resize(1000,600)
        self.setWindowTitle("XY/Histogram/Counts")

        self.max_hist = args.max_hist
        self.bins = [i for i in range(args.max_hist)]

        self.xy_plot = pyqtgraph.PlotWidget()
        self.insertWidget(0, self.xy_plot)
        self.xy_plot_data = None
        self.arrow = None
        self.selected_index = None

        self.hist_plot = pyqtgraph.PlotWidget()
        self.hist_plot_data = None
        split2 = QtWidgets.QSplitter(Qt.Vertical)
        self.insertWidget(1, split2)

        split2.insertWidget(0, self.hist_plot)

        self.counts_plot = pyqtgraph.PlotWidget()
        self.counts_plot_data = None

        split2.insertWidget(1, self.counts_plot)

        self.args = args

    def _set_full_data(self, x, counts, threshold):
        self.xy_plot.clear()
        self.hist_plot.clear()
        self.counts_plot.clear()
        self.xy_plot_data = None
        self.counts_plot_data = None
        self.hist_plot_data = None
        self.indicator = None
        self.selected_index = None

        y, y_upper_err, y_lower_err = _threshold_counts(counts, threshold)
        hists = _histogram_counts(counts, self.bins)
        self.xy_plot_data = self.xy_plot.plot(x=x, y=y,
                                              pen=None,
                                              symbol="x")
        errbars = pyqtgraph.ErrorBarItem(
                x=np.array(x), y=np.array(y), top=np.array(y_upper_err), bottom=np.array(y_lower_err))
        self.xy_plot.addItem(errbars)
        self.xy_plot.setYRange(0,1)
        self.xy_plot.showGrid(x=True,y=True)
        self.xy_plot_data.sigPointsClicked.connect(self._point_clicked)
        for index, (point, counts, hist) in (
                enumerate(zip(self.xy_plot_data.scatter.points(),
                              counts, hists))):
            point.histogram_index = index
            point.counts = counts
            point.hist = hist

        self.hist_plot_data = self.hist_plot.plot(
            stepMode=True, fillLevel=0,
            brush=(0, 0, 255, 150))
        self.hist_plot.addLine(x=threshold)
        self.hist_plot.setXRange(0,self.max_hist)

        self.counts_plot_data = self.counts_plot.plot(pen=None, symbol="x")
        self.counts_plot.addLine(y=threshold)
        self.counts_plot.setYRange(0,self.max_hist)
        self._point_clicked(None, [self.xy_plot_data.scatter.points()[-1]])

    def _point_clicked(self, data_item, spot_items):
        spot_item = spot_items[0]
        position = spot_item.pos()
        if self.indicator is None:
            self.indicator = pyqtgraph.ScatterPlotItem(symbol="o", brush=None, size=10, 
                pen=pyqtgraph.mkPen('y', width=2), pos=[position])
            self.xy_plot.addItem(self.indicator)
        else:
            self.indicator.clear()
            self.indicator.setData(pos=[position])
        self.selected_index = spot_item.histogram_index
        self.hist_plot_data.setData(x=self.bins,
                                    y=spot_item.hist)
        self.counts_plot_data.setData(x=[i for i in range(len(spot_item.counts))],
                                    y=spot_item.counts)

    def keyPressEvent(self, event):
        if self.selected_index is None:
            return
        if event.key() == Qt.Key_Left:
            if self.selected_index == 0:
                return
            ind = self.selected_index-1
        elif event.key() == Qt.Key_Right:
            if self.selected_index == len(self.xy_plot_data.scatter.points())-1:
                return
            ind = self.selected_index+1
        else:
            return
        self._point_clicked(None, [self.xy_plot_data.scatter.points()[ind]])


    def data_changed(self, data, mods):
        try:
            counts = data[self.args.counts][1]
            if self.args.x is not None:
                x = data[self.args.x][1]
            else:
                x = [i for i in range(len(counts))]
            
            threshold = data[self.args.threshold][1]
        except KeyError:
            return
        self._set_full_data(x, counts, threshold)



def main():
    applet = SimpleApplet(XYHistPlot)
    applet.add_dataset("x", "1D array of point abscissas", required=False)
    applet.add_dataset("counts",
                       "2D array of counts, a vector for each point")
    applet.add_dataset("threshold", "threshold for counts", required=True)
    applet.argparser.add_argument("--max_hist", default=250, type=int,
            help="maximum count for histogram")

    applet.run()

if __name__ == "__main__":
    main()
