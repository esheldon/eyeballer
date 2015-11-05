from __future__ import print_function
import os
import numpy
from numpy import flipud
import fitsio

from . import jpegs
# uncalibrated mags
MINMAG=10
MAXMAG=15

ROW_FIELD='ywin_image'
COL_FIELD='xwin_image'

MAG_FIELD='mag_auto'

PADDING = 10

CHIP_REBIN=4

# this bit is larger than the current set of flags
# https://opensource.ncsa.illinois.edu/confluence/display/DESDM/Guide+to+Bad+Pixel+Masks+%28BPMs%29+and+Mask+Bits

WEIGHT_LOWVAL_SVY1 = 0.0001
WEIGHT_BIT=15
WEIGHT_FLAG=2**WEIGHT_BIT

BADPIX_SUSPECT = 2048

class Image(dict):
    def __init__(self, image_file, bkg_file, **keys):
        """
        Load the image, bpm, and weight data. Background subtract

        parameters
        ----------
        image_file: FITS filename
            The image from which to cut
        bkg_file: FITS filename
            The associated background file
        image_ext, bpm_ext, wt_ext, bkg_ext
        """

        self.update(keys)

        self['image_file'] = image_file
        self['bkg_file'] = bkg_file

        self['image_ext'] = self.get('image_ext','sci')
        self['bpm_ext']   = self.get('bpm_ext','msk')
        self['wt_ext']    = self.get('wt_ext','wgt')
        self['bkg_ext']   = self.get('bkg_ext','sci')

        self._load_data()

    def write_jpeg(self, fname, rebin=CHIP_REBIN):
        from . import jpegs
        _make_dir(fname)
        print(fname)
        if rebin:
            imrebin=rebin_image(self.image, rebin)
            jpegs.write_se_jpeg(fname, imrebin)
        else:
            jpegs.write_se_jpeg(fname, self.image)

    def _load_data(self):
        print(self['image_file'])

        with fitsio.FITS(self['image_file']) as fits:
            image = fits[self['image_ext']].read()
            bpm = fits[self['bpm_ext']].read()
            wt = fits[self['wt_ext']].read()

        print(self['bkg_file'])
        bkg=fitsio.read(self['bkg_file'], ext=self['bkg_ext'])

        image -= bkg
        self.bkg=bkg

        self.image=image
        self.bpm=bpm
        self.wt=wt

class EyeballMaker(object):
    def __init__(self, conf, image_file, bkg_file, **keys):
        """
        parameters
        ----------
        image_file: FITS filename
            The image from which to cut
        bkg_file: FITS filename
            The associated background file
        output_file: string
            Name of output file

        rebin: integer, optional
            How much to rebin the image, default CHIP_REBIN
        low_weight: float, optional
            Lower limit for weight map; values below this get
            marked in the bpm.  Default None
        """

        self.conf=conf
        self.image_file=image_file
        self.bkg_file=bkg_file

        self.rebin=conf.get('rebin',CHIP_REBIN)

        self.low_weight=conf.get('low_weight',None)

        self._load_data()

    def write_fits(self, fitsfile, **keys):
        fitsfile=os.path.expandvars(fitsfile)
        fitsfile=os.path.expanduser(fitsfile)

        print(fitsfile)
        _make_dir(fitsfile)

        with fitsio.FITS(fitsfile,'rw',clobber=True) as fits:
            meta = self._get_meta()
            fits.write(meta, extname="metadata")

            print("preparing image")
            tim = self._prepare_image(**keys)
            fits.write(tim, extname="field")

            print("preparing combined bpm")
            tbpm = self._prepare_combined_bpm(**keys)

            print("writing data")
            fits.write(tbpm, extname="bpm_and_weight")

    def _prepare_image(self):

        if self.rebin <= 1:
            imrebin=self.image_obj.image
        else:
            imrebin=rebin_image(self.image_obj.image, self.rebin)

        imout = flipud(imrebin)
        imout = imout.transpose()
        return imout

    def _prepare_combined_bpm(self):

        bpm=self.image_obj.bpm.copy()

        if self.low_weight is not None:
            wt_low = numpy.where(self.image_obj.wt < WEIGHT_LOWVAL_SVY1)

            if wt_low[0].size > 0:
                bpm[wt_low] |= WEIGHT_FLAG

        if self.rebin <= 1:
            bpm_rebin=bpm
        else:
            bpm_rebin= rebin_bitmask_or(bpm, self.rebin)

        imout = flipud(bpm_rebin)
        imout = imout.transpose()
        return imout


    def _get_meta(self):

        istr='S%d' % len(self.image_file)
        bstr='S%d' % len(self.bkg_file)

        metadt=[('image_file',istr),
                ('bkg_file',bstr)]


        meta=numpy.zeros(1, dtype=metadt)
        meta['image_file']=self.image_file
        meta['bkg_file']=self.bkg_file

        return meta


    def _load_data(self):
        imobj=Image(self.image_file, self.bkg_file, **self.conf)

        self.image_obj=imobj


def _make_dir(fname):
    dir=os.path.dirname(fname)
    if not os.path.exists(dir):
        print('making directory:',dir)
        try:
            os.makedirs(dir)
        except:
            # probably a race condition
            pass


def _string_to_int(s):
    """
    Just take first ten digits
    """
    #ord3 = lambda x : '%.3d' % ord(x)
    #return int(''.join(map(ord3, s)))
    ord0 = lambda x : '%d' % ord(x)
    ival=int(''.join(map(ord0, s)))
    return ival

def or_elements(arr):
    x = 0
    for xi in arr.flat:
        x |= xi

    return x

def rebin_bitmask_or(a, rebin_fac):
    """
    rebin using builting array methods

    a.reshape(args[0],factor[0],).mean(1) 
    a.reshape(args[0],factor[0],args[1],factor[1],).mean(1).mean(2)
    """
    from numpy import asarray

    shape = a.shape

    newshape = asarray(shape)/rebin_fac
    factor = asarray(shape)/newshape

    rs_a = a.reshape(newshape[0],factor[0],newshape[1],factor[1])

    new_a1 = numpy.zeros( (newshape[0], newshape[1], factor[1]), dtype=a.dtype)

    for i0 in xrange(newshape[0]):
        for i2 in xrange(newshape[1]):
            for i3 in xrange(factor[1]):
                new_a1[i0,i2,i3] = or_elements(rs_a[i0,:,i2,i3])

    new_a2 = numpy.zeros( (newshape[0], newshape[1]), dtype=a.dtype)
    for i0 in xrange(newshape[0]):
        for i1 in xrange(newshape[1]):
            new_a2[i0,i1] = or_elements(new_a1[i0,i1,:])

    return new_a2

def rebin_image(im, factor, dtype=None):
    """
    Rebin the image so there are fewer pixels.  The pixels are simply
    averaged.
    """
    factor=int(factor)
    s = im.shape
    if ( (s[0] % factor) != 0
            or (s[1] % factor) != 0):
        raise ValueError("shape in each dim (%d,%d) must be "
                   "divisible by factor (%d)" % (s[0],s[1],factor))

    newshape=numpy.array(s)/factor
    if dtype is None:
        a=im
    else:
        a=im.astype(dtype)

    return a.reshape(newshape[0],factor,newshape[1],factor,).sum(1).sum(2)/factor/factor

def boost_image( a, factor):
    """
    Resize an array to larger shape, simply duplicating values.
    """
    from numpy import mgrid

    factor=int(factor)
    if factor < 1:
        raise ValueError("boost factor must be >= 1")

    newshape=numpy.array(a.shape)*factor

    slices = [ slice(0,old, float(old)/new) for old,new in zip(a.shape,newshape) ]
    coordinates = mgrid[slices]
    indices = coordinates.astype('i')   #choose the biggest smaller integer index
    return a[tuple(indices)]


