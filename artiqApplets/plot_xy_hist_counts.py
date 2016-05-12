#!/usr/bin/env python3.5

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
import pyqtgraph

from artiq.applets.simple import SimpleApplet


def _compute_ys(histogram_bins, histograms_counts):
        bin_centers = np.empty(len(histogram_bins)-1)
        for i in range(len(bin_centers)):
            bin_centers[i] = (histogram_bins[i] + histogram_bins[i+1])/2
        ys = np.empty(histograms_counts.shape[0])
        for n, counts in enumerate(histograms_counts):
            ys[n] = sum(counts)/len(counts)
        return ys

def _threshold_counts(counts, threshold):
    y = []
    for countVec in counts:
        p = sum([x >= threshold for x in countVec]) / len(countVec)
        y.append(p)
    return y

def _histogram_counts(counts, histogram_bins):
    hists = []
    for countVec in counts:
        hist, bins = np.histogram(countVec, bins=histogram_bins)
        hists.append(hist)
    return hists


class XYHistPlot(QtWidgets.QSplitter):
    def __init__(self, args):
        QtWidgets.QSplitter.__init__(self)
        self.resize(1000,600)
        self.setWindowTitle("XY/Histogram")

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

    def _set_full_data(self, x, counts, histogram_bins, threshold):
        self.xy_plot.clear()
        self.hist_plot.clear()
        self.counts_plot.clear()
        self.xy_plot_data = None
        self.counts_plot_data = None
        self.hist_plot_data = None
        self.arrow = None
        self.selected_index = None

        self.histogram_bins = histogram_bins

        y = _threshold_counts(counts, threshold)
        hists = _histogram_counts(counts, histogram_bins)
        self.xy_plot_data = self.xy_plot.plot(x=x, y=y,
                                              pen=None,
                                              symbol="x")
        #self.xy_plot_data.disableAutoRange(axis=pyqtgraph.ViewBox.XAxis)
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
        self.counts_plot_data = self.counts_plot.plot(pen=None, symbol="x")
        self.counts_plot.addLine(y=threshold)
        self._point_clicked(None, [self.xy_plot_data.scatter.points()[-1]])

    def _point_clicked(self, data_item, spot_items):
        spot_item = spot_items[0]
        position = spot_item.pos()
        if self.arrow is None:
            self.arrow = pyqtgraph.ArrowItem(
                angle=-120, tipAngle=30, baseAngle=20, headLen=40,
                tailLen=40, tailWidth=8, pen=None, brush="y")
            self.arrow.setPos(position)
            # NB: temporary glitch if addItem is done before setPos
            self.xy_plot.addItem(self.arrow)
        else:
            self.arrow.setPos(position)
        self.selected_index = spot_item.histogram_index
        self.hist_plot_data.setData(x=self.histogram_bins,
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
            if self.args.histogram_bins is not None:
                histogram_bins = data[self.args.histogram_bins][1]
            else:
                histogram_bins = [i for i in range(300)]
            if self.args.threshold is not None:
                threshold = int(self.args.threshold) #data[self.args.threshold][1]
            else:
                threshold = data["singleIon.threshold"][1]
        except KeyError:
            return
        self._set_full_data(x, counts, histogram_bins, threshold)


def main():
    applet = SimpleApplet(XYHistPlot)
    applet.add_dataset("x", "1D array of point abscissas", required=False)
    applet.add_dataset("counts",
                       "2D array of counts, for each point")
    applet.add_dataset("histogram_bins",
                       "1D array of histogram bin boundaries", required=False)
    applet.add_dataset("threshold", "threshold for counts", required=False)
    applet.run()

if __name__ == "__main__":
    main()
