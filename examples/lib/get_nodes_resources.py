# Import the required datetime functions
from prometheus_api_client import PrometheusConnect, MetricSnapshotDataFrame, MetricRangeDataFrame
from prometheus_api_client.utils import parse_datetime
import datetime as dt
import pandas as pd

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
    
        return [finalTime, freeCPU]
