# Import the required datetime functions
from lib import get_nodes_resources


cpu = get_nodes_resources.get_resources(instance='10.1.4.43:9100', url="http://10.1.4.71:9090")
freeCPU = cpu.get_free_cpu()

print(freeCPU)


