#!/usr/bin/env python3.5

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
import pyqtgraph
from scipy.stats import binom

from artiq.applets.simple import SimpleApplet


def _threshold_counts(counts, thresholdLow, thresholdHigh, n_vec):
    y11 = []
    y11_upper_err = []
    y11_lower_err = []
    y10_01 = []
    y10_01_upper_err = []
    y10_01_lower_err = []
    y00 = []
    y00_upper_err = []
    y00_lower_err = []
    for countVec, N in zip(counts, n_vec):
        countVec = countVec[0:int(N)]
        p11 = sum([x >= thresholdHigh for x in countVec]) / N
        p10_01 = sum([((x < thresholdHigh) & (x > thresholdLow)) for x in countVec]) / N
        p00 = sum([x <= thresholdLow for x in countVec]) / N
        y11.append(p11)
        y10_01.append(p10_01)
        y00.append(p00)
        kci11 = binom.interval(0.68, N, p11) 
        kci10_01 = binom.interval(0.68, N, p10_01) 
        kci00 = binom.interval(0.68, N, p00) 
        y11_lower_err.append( p11 - kci11[0]/N )
        y11_upper_err.append( kci11[1]/N - p11 )
        y10_01_lower_err.append( p10_01 - kci10_01[0]/N )
        y10_01_upper_err.append( kci10_01[1]/N - p10_01 )
        y00_lower_err.append( p00 - kci00[0]/N )
        y00_upper_err.append( kci00[1]/N - p00 )
    return y11, y11_upper_err, y11_lower_err, y00, y00_upper_err, y00_lower_err, y10_01, y10_01_upper_err, y10_01_lower_err

def _histogram_counts(counts, bins):
    hists = []
    for countVec in counts:
        hist, bins = np.histogram(countVec, bins=bins)
        hists.append(hist)
    return hists


class XYHistPlot2Ions(QtWidgets.QSplitter):
    def __init__(self, args):
        QtWidgets.QSplitter.__init__(self)
        self.resize(1000,600)
        self.setWindowTitle("XY/Histogram")

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

    def _set_full_data(self, x, counts, thresholdLow, thresholdHigh, n_vec):
        self.xy_plot.clear()
        self.hist_plot.clear()
        self.counts_plot.clear()
        self.xy_plot_data = None
        self.counts_plot_data = None
        self.hist_plot_data = None
        self.indicator = None
        self.selected_index = None

        y11, y11_upper_err, y11_lower_err, y00, y00_upper_err, y00_lower_err, y10_01, y10_01_upper_err, y10_01_lower_err = _threshold_counts(counts, thresholdLow, thresholdHigh, n_vec)
        hists = _histogram_counts(counts, self.bins)
        self.xy_plot_data = self.xy_plot.plot(x=x, y=y11,pen=None,symbol="x")
        self.xy_plot.plot(x, y10_01)
        errbars11 = pyqtgraph.ErrorBarItem(
                x=np.array(x), y=np.array(y11), top=np.array(y11_upper_err), bottom=np.array(y11_lower_err))
        errbars10_01 = pyqtgraph.ErrorBarItem(
                x=np.array(x), y=np.array(y10_01), top=np.array(y10_01_upper_err), bottom=np.array(y10_01_lower_err))
        self.xy_plot.addItem(errbars11)
        self.xy_plot.addItem(errbars10_01)
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
        self.hist_plot.addLine(x=thresholdLow)
        self.hist_plot.addLine(x=thresholdHigh)
        self.hist_plot.setXRange(0,self.max_hist)

        self.counts_plot_data = self.counts_plot.plot(pen=None, symbol="x")
        self.counts_plot.addLine(y=thresholdLow)
        self.counts_plot.addLine(y=thresholdHigh)
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
            n_vec = data[self.args.Nvec][1]
            #print(counts)
            #print(n_vec)
            if self.args.x is not None:
                x = data[self.args.x][1]
            else:
                x = [i for i in range(len(counts))]
            thresholdLow = data[self.args.thresholdLow][1]
            thresholdHigh = data[self.args.thresholdHigh][1]
            #print(threshold)
        except KeyError:
            return
        
        if len(counts) != len(x) or len(counts) != len(n_vec):
            return
        
        self._set_full_data(x, counts, thresholdLow, thresholdHigh, n_vec)



def main():
    applet = SimpleApplet(XYHistPlot2Ions)
    applet.add_dataset("x", "1D array of point abscissas", required=False)
    applet.add_dataset("counts", "counts vector", required=True)
    applet.add_dataset("Nvec", "shots per scan point", required=True)
    applet.add_dataset("thresholdLow", "low threshold for counts", required=True)
    applet.add_dataset("thresholdHigh", "high threshold for counts", required=True)
    applet.argparser.add_argument("--max_hist", default=250, type=int,
            help="maximum count for histogram")


    applet.run()

if __name__ == "__main__":
    main()