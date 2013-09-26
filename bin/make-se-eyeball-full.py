"""
    %prog [options] image bkg cat fitsfile mosaic_jpg field_jpg2 field_jpg4

Make a FITS file with cutouts from the indicated image.  Bright objects
are chosen from the catalog.

Also write a jpeg of the entire ccd
"""
import sys, os
from optparse import OptionParser
from eyeballer.cutouts import EyeballMaker, CHIP_REBIN, MOSAIC_BOOST

parser=OptionParser(__doc__)

parser.add_option('-s','--size',default=32,
                  help="cutout size, default %default")
parser.add_option('-n','--ncutout',default=100,
                  help="number of cutouts, default %default")
parser.add_option('--boost',default=MOSAIC_BOOST,
   help="Boost the cutout mosaic images by this factor.  %default")

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

    if len(args) < 7:
        parser.print_help()
        sys.exit(1)

    image=args[0]
    bkg=args[1]
    cat=args[2]
    fitsfile=args[3]
    mosaic_jpg=args[4]
    field_jpg2=args[5]
    field_jpg4=args[6]

    if '.fz' not in fitsfile:
        raise ValueError("expected .fz fits file name")
    tmp_fitsfile=fitsfile.replace('.fz','')

    cutout_size=int(options.size)
    ncutout=int(options.ncutout)
    boost=int(options.boost)

    cutmaker=EyeballMaker(image_file=image,
                         bkg_file=bkg,
                         cat_file=cat,
                         cutout_size=cutout_size,
                         ncutout=ncutout)

    cutmaker.write_fits(tmp_fitsfile, rebin=CHIP_REBIN)
    cutmaker.write_mosaic_jpeg(mosaic_jpg, boost=boost)

    cutmaker.image_obj.write_jpeg(field_jpg2, rebin=2)
    cutmaker.image_obj.write_jpeg(field_jpg4, rebin=4)

    fpack_file(tmp_fitsfile, fitsfile)


main()
