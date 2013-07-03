"""
    %prog [options] image bkg cat fitsfile

Make a FITS file with a reduced version of the field and
some metadata, as well as the bpm and a bit for ~zero weight.

to write more stuff, including jpegs, see make-se-eyeball-full.py
"""
import sys, os
from optparse import OptionParser
from eyeballer.cutouts import EyeballMaker, CHIP_REBIN

parser=OptionParser(__doc__)

def fpack_file(tmp_fitsfile, fitsfile):

    print 'fpacking:',fitsfile
    if os.path.exists(fitsfile):
        os.remove(fitsfile)

    ret=os.system('fpack %s' % tmp_fitsfile)
    if ret != 0:
        raise ValueError("Error fpacking file")

    if not os.path.exists(fitsfile):
        raise ValueError("fpacked filem missing: %s" % fitsfile)
    print 'removing:',tmp_fitsfile
    os.remove(tmp_fitsfile)

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
