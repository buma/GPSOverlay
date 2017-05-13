
def write_run(seq_name, file_name):
    mf = "\nmplayer mf://{} -mf fps=8 -vo xv\n"
    with open(file_name, "wt") as out_seq_file:
        out_seq_file.write("#!/bin/sh\n")
        out_seq_file.write(mf.format(seq_name))
