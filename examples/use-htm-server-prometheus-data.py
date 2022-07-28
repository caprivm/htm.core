# Import the required datetime functions
from lib import get_nodes_resources
from lib import htm_rest_api
import sys
import pandas as pd
import time

inputs = []
anomaly = []
anomalyProb = []
predictions = []
scaleFactor = 1024
iterations = 1000

def main(verbose=False, id=sys.argv[1]):

    # Call REST in HTM
    net = htm_rest_api.NetworkREST(id=id, verbose=verbose)     # The ID is the id of the HTM created in build-htm

    # Loop
    for itr in range(iterations):
        
        # Get resource
        # cpu = get_nodes_resources.get_resources(instance='10.1.4.43:9100', url="http://10.1.4.71:9090")
        record = pd.DataFrame(get_nodes_resources.get_resources(instance='10.1.4.43:9100', url="http://10.1.4.71:9090").get_free_cpu(), columns =["timestamp", "freeCPU"])
        
        # Convert data value string into float
        consumption = float(record["freeCPU"]) * scaleFactor
        inputs.append(consumption)

        # Put region param
        net.put_region_param('dateEncoder', 'sensedTime', int(record["timestamp"]))
        net.put_region_param('scalarEncoder', 'sensedValue', consumption)
        net.input('clsr_bucket', consumption)

        # Predict what will happen, and then train the predictor based on what just happened.
        net.run()
        pred = htm_rest_api.get_classifer_predict(net, 'clsr')
        pred["anomaly"] = net.get_region_output('tm','anomaly')[0]
        if pred.get('title'):
          predictions.append(pred['title'])
        else:
          predictions.append(float('nan'))

        anomaly.append(pred['anomaly'])
        anomalyProb.append(pred['prob'])

        time.sleep(15)

        # Prints
        print(record,pred)
        
if __name__ == "__main__":
  main()
