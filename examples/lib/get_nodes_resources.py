# Import the required datetime functions
from prometheus_api_client import PrometheusConnect, MetricSnapshotDataFrame, MetricRangeDataFrame
from prometheus_api_client.utils import parse_datetime
import datetime as dt
import pandas as pd
import math

# Config time window
startTime = parse_datetime("15s")
endTime = parse_datetime("now")
chunkSize = dt.timedelta(seconds=15)

class get_resources(object):
    def __init__(self,
                 instance,
                 url,
                 disable_ssl=True):

        self.instance    = instance
        self.url         = url
        self.disable_ssl = disable_ssl

    def get_free_cpu(self):

        # Connect to the Prometheus server
        prom = PrometheusConnect(url=self.url, disable_ssl=self.disable_ssl)
        
        cpuMetrics = ["mode='idle'",
                      "mode='system'",
                      "mode='user'",
                      "mode='iowait'",
                      "mode=~'.*irq'",
                      "mode!='idle',mode!='user',mode!='system',mode!='iowait',mode!='irq',mode!='softirq'"]
        cpuPerformance = []
        mode = 0

        # Get the CPU performance
        for modeMetric in cpuMetrics:
            
            # Custom queries to Prometheus
            if mode == 0:
                cpuRateValue = float(prom.custom_query(query="sum by (mode) (rate(node_cpu_seconds_total{"+modeMetric+",instance='"+self.instance+"',job='node'}[1m0s] offset 15s))")[0]["value"][1]) * 100
            elif mode == 5:
                cpuRateValue = float(prom.custom_query(query="sum (rate(node_cpu_seconds_total{"+modeMetric+",instance='"+self.instance+"',job='node'}[1m0s] offset 15s))")[0]["value"][1]) * 100
            else:
                cpuRateValue = float(prom.custom_query(query="sum by (instance) (rate(node_cpu_seconds_total{"+modeMetric+",instance='"+self.instance+"',job='node'}[1m0s] offset 15s))")[0]["value"][1]) * 100
            
            cpuPerformance.append(cpuRateValue)
            mode = mode + 1

        # Get data example to have timestamp
        metric_data = prom.get_metric_range_data(
            "node_cpu_seconds_total{"+modeMetric+",instance='"+self.instance+"',job='node'}",
            start_time  = startTime,
            end_time    = endTime,
            chunk_size  = chunkSize,
        )
        metric_df = pd.DataFrame(data=MetricSnapshotDataFrame(metric_data))

        # Get final values
        finalTime       = metric_df["timestamp"][0]
        freeCPU         = (cpuPerformance[0]/sum(cpuPerformance)) * 100
    
        return [[dt.datetime.timestamp(finalTime), freeCPU]]

    def get_free_cpu_historical(self, period):

        # Connect to the Prometheus server
        prom = PrometheusConnect(url=self.url, disable_ssl=self.disable_ssl)

        cpuMetrics = ["mode='idle'",
                      "mode='system'",
                      "mode='user'",
                      "mode='iowait'",
                      "mode=~'.*irq'",
                      "mode!='idle',mode!='user',mode!='system',mode!='iowait',mode!='irq',mode!='softirq'"
                      ]
        cpuModes = ["idle", "system", "user", "~iowait", ".*irq", "other"]
        mode = 0

        # Get the CPU performance
        for modeMetric in cpuMetrics:
            if mode == 0:
                # Custom queries to Prometheus
                cpuRateValue = pd.DataFrame(prom.custom_query(query="(sum by (mode) (rate(node_cpu_seconds_total{"+modeMetric+",instance='"+self.instance+"',job='node'}[1m0s])))["+period+":15s]")[0]["values"])
                cpuRateValue.columns = ["timestamp",cpuModes[mode]]
                cpuRateValue[cpuModes[mode]] = pd.to_numeric(cpuRateValue[cpuModes[mode]])
            elif mode == 5:
                cpuRateValueTemp = pd.DataFrame(prom.custom_query(query="(sum (rate(node_cpu_seconds_total{"+modeMetric+",instance='"+self.instance+"',job='node'}[1m0s])))["+period+":15s]")[0]["values"])
                cpuRateValueTemp.columns = ["timestamp",cpuModes[mode]]

                cpuRateValue[cpuModes[mode]] = pd.to_numeric(cpuRateValueTemp[cpuModes[mode]])
            else:
                cpuRateValueTemp = pd.DataFrame(prom.custom_query(query="(sum by (instance) (rate(node_cpu_seconds_total{"+modeMetric+",instance='"+self.instance+"',job='node'}[1m0s])))["+period+":15s]")[0]["values"])
                cpuRateValueTemp.columns = ["timestamp",cpuModes[mode]]
                cpuRateValue[cpuModes[mode]] = pd.to_numeric(cpuRateValueTemp[cpuModes[mode]])

            mode = mode + 1
        
        colList = list(cpuRateValue)
        colList.remove("timestamp")
        cpuRateValue["freeCPU"]     = (cpuRateValue["idle"]/cpuRateValue[colList].sum(axis=1)) * 100

        return cpuRateValue

class get_stats(object):
    def __init__(self,
                 inputs,
                 predictions,
                 scaleFactor):

        self.inputs         = inputs
        self.predictions    = predictions
        self.scaleFactor    = scaleFactor

    def get_rmse(self):
        accuracy = 0
        accuracy_samples = 0

        for idx, inp in enumerate(self.inputs):
            val = float(self.predictions[idx])/self.scaleFactor
            if not math.isnan(val):
                accuracy += (float(inp)/self.scaleFactor - val)**2
                accuracy_samples += 1

        accuracy = (accuracy / accuracy_samples)**.5
        return accuracy
