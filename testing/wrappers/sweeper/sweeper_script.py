import argparse
import doodad.wrappers.sweeper as sweeper

def main(args):
    print(args.n)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, help='Integer to print')
    parser.add_argument('--doodad', action='store_true', help='Launch via doodad')
    args = parser.parse_args()

    if args.doodad:
        sweep_dict = {
            'n': [1,2,3,4]
        }
        sweeper = sweeper.DoodadSweeper(mounts=[])
        sweeper.run_sweep_local(__file__, params)
    else:
        main(args)
