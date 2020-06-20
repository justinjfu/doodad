import argparse

parser = argparse.ArgumentParser(description='Print')
parser.add_argument('--message', type=str,
                    help='message to print')

args = parser.parse_args()
print(args.message)
