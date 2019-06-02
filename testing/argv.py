"""
This script is for testing argument passing into DAR files.

This script will print out each argument passed to it, separated by newlines.
i.e.

python argv.py a1 a2 a3

Output:
a1
a2
a3

"""
import sys
for i in range(1,len(sys.argv)):
    print(sys.argv[i])
