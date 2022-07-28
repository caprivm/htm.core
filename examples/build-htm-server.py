import csv
import datetime
import os
import numpy as np
import math

from lib import htm_rest_api

# URL of the HTM server
host = '127.0.0.1'                  # Get local machine IP, the default.
port = 8050                         # The default port
URL = 'http://'+host+':'+str(port)

default_parameters = {
  # there are 2 (3) encoders: "value" (RDSE) & "time" (DateTime weekend, timeOfDay)
  'enc': {
    "value": {
      'resolution': 0.88,
      'size': 700,
      'sparsity': 0.02
    },
    "time": {
      'timeOfDay': (30, 1),
      'weekend': 21
    }
  },
  'predictor': {'sdrc_alpha': 0.1},
  'sp': {
    'boostStrength': 3.0,
    'columnCount': 1638,
    'localAreaDensity': 0.04395604395604396,
    'potentialPct': 0.85,
    'synPermActiveInc': 0.04,
    'synPermConnected': 0.13999999999999999,
    'synPermInactiveDec': 0.006
  },
  'tm': {
    'activationThreshold': 17,
    'cellsPerColumn': 13,
    'initialPerm': 0.21,
    'maxSegmentsPerCell': 128,
    'maxSynapsesPerSegment': 64,
    'minThreshold': 10,
    'newSynapseCount': 32,
    'permanenceDec': 0.1,
    'permanenceInc': 0.1
  },
  'anomaly': {
    'likelihood':
        {'probationaryPct': 0.1,
            'reestimationPeriod': 100}
        }
}


def main(parameters=default_parameters, argv=None, verbose=True):
  if verbose:
    import pprint
    print("Parameters:")
    pprint.pprint(parameters, indent=4)
    print("")
  
  # Call REST in HTM
  net = htm_rest_api.NetworkREST(verbose=True)
  # Make the Encoders. These will convert input data into binary representations.
  dateRegion = net.add_region(
    'dateEncoder', 'DateEncoderRegion',
    dict(timeOfDay_width=parameters["enc"]["time"]["timeOfDay"][0],
         timeOfDay_radius=parameters["enc"]["time"]["timeOfDay"][1],
         weekend_width=parameters["enc"]["time"]["weekend"]))

  scalarRegion = net.add_region(
    'scalarEncoder', 'RDSEEncoderRegion',
    dict(size=parameters["enc"]["value"]["size"],
         sparsity=parameters["enc"]["value"]["sparsity"],
         resolution=parameters["enc"]["value"]["resolution"]))

  # Make the HTM. SpatialPooler & TemporalMemory & associated tools.
  spParams = parameters["sp"]
  spRegion = net.add_region(
    'sp',
    'SPRegion',
    dict(
      columnCount=spParams['columnCount'],
      potentialPct=spParams["potentialPct"],
      potentialRadius=0,  # 0 is auto assign as inputWith
      globalInhibition=True,
      localAreaDensity=spParams["localAreaDensity"],
      synPermInactiveDec=spParams["synPermInactiveDec"],
      synPermActiveInc=spParams["synPermActiveInc"],
      synPermConnected=spParams["synPermConnected"],
      boostStrength=spParams["boostStrength"],
      wrapAround=True))

  tmParams = parameters["tm"]
  tmRegion = net.add_region(
    'tm', 'TMRegion',
    dict(columnCount=spParams['columnCount'],
         cellsPerColumn=tmParams["cellsPerColumn"],
         activationThreshold=tmParams["activationThreshold"],
         initialPermanence=tmParams["initialPerm"],
         connectedPermanence=spParams["synPermConnected"],
         minThreshold=tmParams["minThreshold"],
         maxNewSynapseCount=tmParams["newSynapseCount"],
         permanenceIncrement=tmParams["permanenceInc"],
         permanenceDecrement=tmParams["permanenceDec"],
         predictedSegmentDecrement=0.0,
         maxSegmentsPerCell=tmParams["maxSegmentsPerCell"],
         maxSynapsesPerSegment=tmParams["maxSynapsesPerSegment"]))

  clsrRegion = net.add_region('clsr', 'ClassifierRegion', {'learn': True})

  net.add_link(dateRegion, spRegion, 'encoded', 'bottomUpIn')
  net.add_link(scalarRegion, spRegion, 'encoded', 'bottomUpIn')
  net.add_link(spRegion, tmRegion, 'bottomUpOut', 'bottomUpIn')
  net.add_link(tmRegion, clsrRegion, 'bottomUpOut', 'pattern')
  net.add_link(htm_rest_api.INPUT, clsrRegion, 'clsr_bucket', 'bucket', 1)

  net.create()

if __name__ == "__main__":
  main()
