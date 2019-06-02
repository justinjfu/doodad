import argparse

def main(args):
    print(args.n)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, help='Integer to print')
    args = parser.parse_args()
    main(args)
