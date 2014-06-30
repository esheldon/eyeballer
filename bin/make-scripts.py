"""
    %prog [options] run-name
"""
import sys, os
from optparse import OptionParser
parser=OptionParser(__doc__)

def main():
    options, args = parser.parse_args(sys.argv[1:])

    if len(args) != 3:
        parser.print_help()
        sys.exit(1)

    image=args[0]
    bkg=args[1]
    fitsfile=args[2]

    if '.fz' not in fitsfile:
        raise ValueError("expected .fz fits file name")
    tmp_fitsfile=fitsfile.replace('.fz','')

    cutmaker=EyeballMaker(types=['field'],
                          image_file=image,
                          bkg_file=bkg)

    cutmaker.write_fits(tmp_fitsfile, rebin=CHIP_REBIN)
    fpack_file(tmp_fitsfile, fitsfile)


main()
