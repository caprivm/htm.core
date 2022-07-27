import csv
import datetime
import os
import numpy as np
import math
import sys

from lib import htm_rest_api

# Load Data
_EXAMPLE_DIR        = os.path.dirname(__file__)
_INPUT_FILE_PATH    = os.path.join(_EXAMPLE_DIR, "data/inputs/gymdata.csv")
_OUTPUT_FILE_PATH   = os.path.join(_EXAMPLE_DIR, "data/outputs/gymdata-htm-"+str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))+".csv")

# Iterate through every datum in the dataset, record the inputs & outputs.
inputs = []
anomaly = []
anomalyProb = []
predictions = []

def main(verbose=False, id=sys.argv[1]):

  # Read the input file.
  records = []
  with open(_INPUT_FILE_PATH, "r") as fin:
    reader = csv.reader(fin)
    headers = next(reader)
    next(reader)
    next(reader)
    for record in reader:
      records.append(record)

  # Call REST in HTM
  net = htm_rest_api.NetworkREST(id=id, verbose=verbose)     # The ID is the id of the HTM created in build-htm

  # Train HTM
  for count, record in enumerate(records):
    # Convert date string into Python date object.
    dateString = datetime.datetime.strptime(record[0], "%m/%d/%y %H:%M")
    # Convert data value string into float.
    consumption = float(record[1])
    inputs.append(consumption)
    
    # Put region param
    net.put_region_param('dateEncoder', 'sensedTime', int(dateString.timestamp()))
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

  # Calculate the predictive accuracy, Root-Mean-Squared
  accuracy = 0
  accuracy_samples = 0

  for idx, inp in enumerate(inputs):
    val = predictions[idx]
    if not math.isnan(val):
      accuracy += (inp - val)**2
      accuracy_samples += 1

  accuracy = (accuracy / accuracy_samples)**.5
   
  # Write csv with results
  header = ['index', 'inputs', 'predictions', 'anomaly']
  with open(_OUTPUT_FILE_PATH, 'w', newline='') as file:
      writer = csv.writer(file)
      writer.writerow(header)
      for idx, inp in enumerate(inputs):
          data = [idx,inp, predictions[idx], anomaly[idx]]
          writer.writerow(data)

  # Show info about the anomaly (mean & std)
  print("Predictive Error (RMS):", accuracy)
  print("Anomaly Mean", np.mean(anomaly))
  print("Anomaly Std ", np.std(anomaly))

if __name__ == "__main__":
  main()
