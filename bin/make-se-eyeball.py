"""
    %prog [options] image bkg cat cutout_file mosaic_file jpeg_file

Make a FITS file with cutouts from the indicated image.  Bright objects
are chosen from the catalog.

Also write a jpeg of the entire ccd
"""
import sys
from optparse import OptionParser
from eyeballer.cutouts import CutoutMaker

parser=OptionParser(__doc__)

parser.add_option('-s','--size',default=32,
                  help="cutout size, default %default")
parser.add_option('-n','--ncutout',default=100,
                  help="number of cutouts, default %default")

def main():
    options, args = parser.parse_args(sys.argv[1:])

    if len(args) < 6:
        parser.print_help()
        sys.exit(1)

    image=args[0]
    bkg=args[1]
    cat=args[2]
    cutout_file=args[3]
    mosaic_file=args[4]
    jpeg_file=args[5]

    cutout_size=int(options.size)
    ncutout=int(options.ncutout)

    cutmaker=CutoutMaker(image_file=image,
                         bkg_file=bkg,
                         cat_file=cat,
                         cutout_size=cutout_size,
                         ncutout=ncutout)

    cutmaker.write_cutouts(cutout_file, mosaic_file)
    cutmaker.image_obj.write_jpeg(jpeg_file, rebin=4)

main()
