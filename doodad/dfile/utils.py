
def is_read_mode(mode):
    return mode in {'r', 'r+', 'w+'}

def is_write_mode(mode):
    return mode in {'w', 'r+', 'w+'}
