import csv
import datetime
import os
import numpy as np
import sys

from lib import htm_rest_api
from lib import get_nodes_resources

# Load Data
_EXAMPLE_DIR        = os.path.dirname(__file__)
_OUTPUT_FILE_PATH   = os.path.join(_EXAMPLE_DIR, "data/outputs/prometheus-htm-"+str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))+".csv")

# Iterate through every datum in the dataset, record the inputs & outputs.
inputs = []
anomaly = []
anomalyProb = []
predictions = []
scaleFactor = 1024

def get_prometheus_historical_data(instance, url, period):
    
    # Get prometheus information
    cpu = get_nodes_resources.get_resources(instance = instance, url = url)
    return cpu.get_free_cpu_historical(period = period)

def main(verbose=False, id=sys.argv[1], period=sys.argv[2]):

  # Call REST in HTM
  net = htm_rest_api.NetworkREST(id=id, verbose=verbose)     # The ID is the id of the HTM created in build-htm
  
  # Get Prometheus information
  historicalRecords = get_prometheus_historical_data(instance = '10.1.4.43:9100', url = "http://10.1.4.71:9090", period = period)

  # Train HTM
  for index, record in historicalRecords.iterrows():

    # Convert data value string into float.
    consumption = float(record["freeCPU"]) * scaleFactor   # Scale to better learning of HTM
    inputs.append(consumption)
    
    # Put region param
    net.put_region_param('dateEncoder', 'sensedTime', int(record["timestamp"]))
    net.put_region_param('scalarEncoder', 'sensedValue', consumption)
    net.input('clsr_bucket', consumption)

    # Predict what will happen, and then train the predictor based on what just happened.
    net.run()
    pred = htm_rest_api.get_classifer_predict(net, 'clsr')
    pred['anomaly'] = net.get_region_output('tm','anomaly')[0]
    if pred.get('title'):
      predictions.append(pred['title'])
    else:
      predictions.append(float('nan'))

    anomaly.append(pred['anomaly'])
    anomalyProb.append(pred['prob'])

  # Get accuracy
  accuracy = get_nodes_resources.get_stats(inputs, predictions, scaleFactor)
  accuracy = accuracy.get_rmse()

  # Write csv with results
  header = ['index', 'inputs', 'predictions', 'anomaly', 'anomaly_prob']
  with open(_OUTPUT_FILE_PATH, 'w', newline='') as file:
      writer = csv.writer(file)
      writer.writerow(header)
      for idx, inp in enumerate(inputs):
          data = [idx, float(inp)/scaleFactor, float(predictions[idx])/scaleFactor, anomaly[idx], anomalyProb[idx]]
          writer.writerow(data)

  # Show info about the anomaly (mean & std)
  print("Predictive Error (RMS):", accuracy)
  print("Anomaly Mean", np.mean(anomaly))
  print("Anomaly Std ", np.std(anomaly))

if __name__ == "__main__":
  main()
