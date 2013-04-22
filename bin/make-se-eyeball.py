"""
    %prog [options] image bkg cat output_file

Make a FITS file with cutouts from the indicated image.  Bright objects
are chosen from the catalog.
"""
from optparse import OptionParser

parser=OptionParser(usage)

parser.add_option('-s','--size',default=24,
                  help="cutout size, default %default")
parser.add_option('-n','--ncutout',default=100,
                  help="number of cutouts, default %default")

def main():
    options, args = parser.parse_args(sys.argv[1:])

    if len(args) < 4:
        parser.print_help()
        sys.exit(1)

    image=args[0]
    bkg=args[1]
    cat=args[2]
    output_file=args[3]

    cutout_size=int(options.size)
    ncutout=int(options.ncutout)

    maker=CutoutMaker(image_file=image,
                      bkg_file=bkg,
                      cat_file=cat,
                      cutout_size=cutout_size,
                      ncutout=ncutout,
                      output_file)
    maker.write_cutouts()

main()
