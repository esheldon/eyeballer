import os
import numpy
import fitsio

# uncalibrated mags
MINMAG=10
MAXMAG=15

ROW_FIELD='ywin_image'
COL_FIELD='xwin_image'

MAG_FIELD='mag_auto'

class CutoutMaker(object):
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
        self.image_file=keys['image_file']
        self.bkg_file=keys['bkg_file']
        self.cat_file=keys['cat_file']
        self.cutout_size=keys['cutout_size']
        self.ncutout=keys['ncutout']
        self.output_file=keys['output_file']

        self._load_data()
        self._set_centers()

    def write_cutouts(self):
        self._make_dir()

        print 'writing to:',self.output_file
        with fitsio.FITS(self.output_file,'rw',clobber=True) as fits:
            data=self._get_table()
            fits.write(data, extname="center_list")

            print 'writing:',len(self.centers),'centers'
            for cen in self.centers:
                cut=Cutout(self.image, cen, self.cutout_size)
                sub_im=cut.get_subimage()
                cut.write(sub)

    def _get_table(self):
        istr='S%d' % len(self.image_file)
        bstr='S%d' % len(self.bkg_file)
        cstr='S%d' % len(self.cat_file)
        ncen=len(self.centers)

        dt=[('image_file',istr),
            ('bkg_file',bstr),
            ('cat_file',cstr),
            ('cutout_size','i4'),
            ('ncenter','i4'),
            ('cen_row','f4',ncen),
            ('cen_col','f4',ncen)]

        table=numpy.zeros(1, dtype=dt)
        table['image_file']=self.image_file
        table['bkg_file']=self.bkg_file
        table['cat_file']=self.cat_file
        table['cutout_size'] = self.cutout_size
        table['ncenter'] = ncen

        for i,cen in enumerate(self.centers):
            table['cen_row'][i] = cen[0]
            table['cen_col'][i] = cen[1]

        return table

    def _set_centers(self):
        selector=self.CatalogSelector(self.cat,
                                      self.image.shape,
                                      self.cutout_size)
        indices=selector.get_indices()
        if len(indices) == 0:
            raise ValueError("found not centers")

        # select random subset
        s=numpy.random.random(indices.size).argsort()
        s = s[0:self.ncutout]
        indices = indices[s]

        centers=[]
        for ind in indices:
            cen=(self.cat[ROW_FIELD][ind], self.cat[COL_FIELD][ind])
            centers.append( cen )
        
        self.centers=cen

    def _load_data(self):
        image=fitsio.read(self.image_file, ext=1, verbose=True)
        bkg=fitsio.read(self.bkg_file, ext=1, verbose=True)
        image -= bkg

        self.image=image
        self.cat=fitsio.read(self.cat_file,
                             ext=2,
                             lower=True,
                             verbose=True)


    def _make_dir(self):
        dir=os.path.basename(output_file)
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except:
                # probably a race condition
                pass

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
        self.cutout_size

        self._do_select()

    def get_indices(self):
        return self.indices

    def _do_select(self):
        
        collow = cat[COL_FIELD] - self.cutout_size - 10
        colhigh = cat[COL_FIELD] + self.cutout_size - 10
        rowlow = cat[ROW_FIELD] - self.cutout_size - 10
        rowhigh = cat[ROW_FIELD] + self.cutout_size - 10

        w,=numpy.where(  (cat['flags'] == 0)
                       & (cat[MAG_FIELD] > MINMAG)
                       & (cat[MAG_FIELD] < MAXMAG)
                       & (collow > 0)
                       & (colhigh < self.imshape[1])
                       & (rowlow > 0)
                       & (rowhigh < self.imshape[0]) )
        self.indices=w

def get_grid(ntot):
    sq=int(sqrt(ntot))
    if ntot==sq*sq:
        return (sq,sq)
    elif ntot <= sq*(sq+1):
        return (sq,sq+1)
    else:
        return (sq+1,sq+1)



