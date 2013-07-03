import os
import numpy
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
MOSAIC_BOOST=3

WEIGHT_BIT=15
WEIGHT_FLAG=2**WEIGHT_BIT


class Image(object):
    def __init__(self, **keys):
        """
        parameters
        ----------
        image_file: FITS filename
            The image from which to cut
        bkg_file: FITS filename, optional
            The associated background file
        """
        self.image_file=keys['image_file']
        self.bkg_file=keys.get('bkg_file',None)

        self._load_data()

    def get_image(self):
        return self.image

    def write_jpeg(self, fname, rebin=CHIP_REBIN):
        from . import jpegs
        _make_dir(fname)
        print fname
        if rebin:
            import images
            imrebin=images.rebin(self.image, rebin)
            jpegs.write_se_jpeg(fname, imrebin)
        else:
            jpegs.write_se_jpeg(fname, self.image)

    def _load_data(self):
        print self.image_file
        image=fitsio.read(self.image_file, ext=1)
        bpm=fitsio.read(self.image_file, ext=2)
        wt=fitsio.read(self.image_file, ext=3)
        if self.bkg_file is not None:
            print self.bkg_file
            bkg=fitsio.read(self.bkg_file, ext=1)
            image -= bkg
            self.bkg=bkg
        else:
            self.bkg=None

        self.image=image
        self.bpm=bpm
        self.wt=wt

class EyeballMaker(object):
    def __init__(self, **keys):
        """
        parameters
        ----------
        image_file: FITS filename
            The image from which to cut
        bkg_file: FITS filename
            The associated background file
        cat_file: FITS filename
            The associated catalogfile
        cutout_size: int
            size of cutouts (size,size)
        ncutout: int
            Number of cutouts; if we can't find
            this many in the mag limits, that's OK.
        output_file: string
            Name of output file
        """
        self.types=keys['types']

        self.image_file=keys['image_file']
        self.bkg_file=keys['bkg_file']

        self.cutout_size=keys.get('cutout_size',None)
        self.ncutout=keys.get('ncutout',None)

        if 'cutouts' in self.types:
            self.docut=True
        else:
            self.docut=False

        self._load_data()

        if self.docut:
            self.cat_file=keys['cat_file']

            self._set_seed()
            self._set_centers()
            self._make_mosaic()

    def write_fits(self, fitsfile, **keys):
        print fitsfile
        _make_dir(fitsfile)

        with fitsio.FITS(fitsfile,'rw',clobber=True) as fits:
            meta = self._get_meta()
            fits.write(meta, extname="metadata")

            if self.docut:
                cendata=self._get_cen_table()
                fits.write(cendata, extname="centers")
                fits.write(self.mosaic, extname="mosaic")

            tim = self._prepare_image(**keys)
            fits.write(tim, extname="field")

            tbpm = self._prepare_combined_bpm(**keys)
            fits.write(tbpm, extname="bpm_and_weight")

    def write_mosaic_jpeg(self, mosaic_jpg, boost=MOSAIC_BOOST):
        """
        Writeout jpeg version of mosaic
        """
        import images
        print mosaic_jpg
        _make_dir(mosaic_jpg)
        m=images.boost(self.mosaic, boost)
        jpegs.write_se_jpeg(mosaic_jpg, m)


    def _prepare_image(self, rebin=CHIP_REBIN):
        from numpy import flipud
        import images
        if rebin <= 1:
            imrebin=self.image
        else:
            imrebin=images.rebin(self.image, rebin)
        
        imout = flipud(imrebin)
        imout = imout.transpose()
        return imout

    def _prepare_combined_bpm(self, rebin=CHIP_REBIN):
        from numpy import flipud
        import images

        bpm=self.bpm.copy()
        wt_low = numpy.where(self.wt < 0.0001)

        if wt_low[0].size > 0:
            bpm[wt_low] |= WEIGHT_FLAG

        if rebin <= 1:
            bpm_rebin=bpm
        else:
            bpm_rebin= rebin_bitmask_or(bpm, rebin)

        imout = flipud(bpm_rebin)
        imout = imout.transpose()
        return imout



    def _add_to_mosaic(self, cutout, i):

        row=i/self.mcols
        col=i % self.mcols

        row1 = row*self.cutout_size
        row2 = (row+1)*self.cutout_size
        col1 = col*self.cutout_size
        col2 = (col+1)*self.cutout_size

        self.mosaic[row1:row2, col1:col2] = cutout

    def _make_mosaic(self):
        """
        Make the mosaic and set the row,col grid
        """
        ntot=len(self.centers)
        nrows,ncols=get_grid(ntot)

        self.mrows=nrows
        self.mcols=ncols
        totrows=self.mrows*self.cutout_size
        totcols=self.mcols*self.cutout_size
        self.mosaic=numpy.zeros((totrows,totcols), dtype='f4')

        for i, cen in enumerate(self.centers):
            cut=Cutout(self.image, cen, self.cutout_size)
            sub_im=cut.get_subimage()
            self._add_to_mosaic(sub_im, i)


    def _get_meta(self):

        istr='S%d' % len(self.image_file)
        bstr='S%d' % len(self.bkg_file)

        metadt=[('image_file',istr),
                ('bkg_file',bstr)]


        if self.docut:
            cstr='S%d' % len(self.cat_file)
            metadt+=[('cat_file',cstr),
                     ('cutout_size','i4'),
                     ('ncutout','i4')]

        meta=numpy.zeros(1, dtype=metadt)
        meta['image_file']=self.image_file
        meta['bkg_file']=self.bkg_file

        if self.docut:
            meta['cat_file']=self.cat_file
            meta['cutout_size'] = self.cutout_size
            meta['ncutout'] = ncen

        return meta



    def _get_cen_table(self):
        ncen=len(self.centers)

        cendt=[('index','i4'),
               ('cen_row','f4'),
               ('cen_col','f4')]

        cendata=numpy.zeros(ncen, dtype=cendt)

        for i,cen in enumerate(self.centers):
            cendata['index'][i] = self.indices[i]
            cendata['cen_row'][i] = cen[0]
            cendata['cen_col'][i] = cen[1]

        return cendata

    def _set_centers(self):
        # always want same random set for given image
        numpy.random.seed(self._seed) 

        selector=CatalogSelector(self.cat,
                                 self.image.shape,
                                 self.cutout_size)
        indices=selector.get_indices()
        if len(indices) == 0:
            raise ValueError("found no good centers")

        # select random subset
        s=numpy.random.random(indices.size).argsort()
        s = s[0:self.ncutout]
        indices = indices[s]
        indices.sort()

        centers=[]
        for i in indices:
            cen=(self.cat[ROW_FIELD][i]-1,
                 self.cat[COL_FIELD][i]-1)
            centers.append( cen )
        
        self.indices=indices
        self.centers=centers

    def _load_data(self):
        imobj=Image(image_file=self.image_file,
                    bkg_file=self.bkg_file)

        self.image_obj=imobj
        self.image=imobj.image
        self.bpm=imobj.bpm
        self.wt=imobj.wt
        if self.docut:
            self.cat=fitsio.read(self.cat_file,
                                 ext=2,
                                 lower=True,
                                 verbose=True)


    def _set_seed(self):
        bname=os.path.basename(self.image_file)
        bname=bname.replace('DECam_','')
        bname=bname.replace('.fits.fz','')
        bname=bname.replace('.fits','')
        # skip leading 00
        bname=bname[2:]

        self._seed = _string_to_int(bname)
        print 'seed:',self._seed

class Cutout(object):
    def __init__(self, image, cen, size):
        self.image=image
        self.cen=cen
        self.size=size
        self._make_cutout()

    def get_subimage(self):
        return self.subimage

    def get_subcen(self):
        return self.subcen

    def _make_cutout(self):
        sh=self.image.shape
        cen=self.cen
        size=self.size

        if (cen[0] < 0 or cen[1] < 0
                or cen[0] > (sh[0]-1)
                or cen[1] > (sh[1]-1) ):
            mess=("center [%s,%s] is out of "
                  "bounds of image: [%s,%s] ")
            mess=mess % (cen[0],cen[1],sh[0],sh[1])
            raise ValueError(mess)

        sz2 = (size-1)/2.
        minrow=int(cen[0]-sz2 )
        maxrow=int(cen[0]+sz2)
        mincol=int(cen[1]-sz2)
        maxcol=int(cen[1]+sz2)
 
        if minrow < 0:
            minrow=0
        if maxrow > (sh[0]-1):
            maxrow=sh[0]-1

        if mincol < 0:
            mincol=0
        if maxcol > (sh[1]-1):
            maxcol=sh[1]-1
        
        # note +1 for python slices
        self.subimage=self.image[minrow:maxrow+1, mincol:maxcol+1].copy()
        self.subcen=[cen[0]-minrow, cen[1]-mincol]

        self.row_range=[minrow,maxrow]
        self.col_range=[mincol,maxcol]

class CatalogSelector(object):
    def __init__(self, cat, imshape, cutout_size):
        self.cat=cat
        self.imshape=imshape
        self.cutout_size=cutout_size

        self._do_select()

    def get_indices(self):
        return self.indices

    def _do_select(self):
        
        cat=self.cat

        row=cat[ROW_FIELD]-1
        col=cat[COL_FIELD]-1

        rad=self.cutout_size/2

        rowlow  = row - rad - PADDING
        rowhigh = row + rad + PADDING
        collow  = col - rad - PADDING
        colhigh = col + rad + PADDING

        w,=numpy.where(  (cat['flags'] == 0)
                       & (cat[MAG_FIELD] > MINMAG)
                       & (cat[MAG_FIELD] < MAXMAG)
                       & (rowlow > 0)
                       & (rowhigh < self.imshape[0])
                       & (collow > 0)
                       & (colhigh < self.imshape[1]) )
        self.indices=w

def get_grid(ntot):
    from math import sqrt
    sq=int(sqrt(ntot))
    if ntot==sq*sq:
        return (sq,sq)
    elif ntot <= sq*(sq+1):
        return (sq,sq+1)
    else:
        return (sq+1,sq+1)


def _make_dir(fname):
    dir=os.path.dirname(fname)
    if not os.path.exists(dir):
        print 'making directory:',dir
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


