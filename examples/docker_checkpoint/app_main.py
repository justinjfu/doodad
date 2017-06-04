import os
import time
import subprocess

import poodag as pd

print('Launching app_main!')

# These are arguments passed in from launch_python
args_dict = pd.get_args()
print('My args are:', args_dict)

k = 0
while True:
    k += 1
    subprocess.call('echo %d' % k, shell=True)    
    time.sleep(1.0)

# Test proper mounting
print('Done!')

