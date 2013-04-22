# tuned for a r band 90 second exposure
NOMINAL_EXPTIME=90.0
SCALE=.004
NONLINEAR=.16

def write_se_jpeg(fname, image, **keys):
    imout = scale_se_image(im, **keys)
    write_jpg(fname, imout, quality=90)

def scale_se_image(im, 
                   exptime=NOMINAL_EXPTIME, 
                   scale=SCALE, 
                   nonlinear=NONLINEAR, 
                   nominal_exptime=NOMINAL_EXPTIME):
    """
    An asinh stretch is applied.
    
    The default nonlinear factor and scale are appropriate for an r-band
    90 second exposure.  Enter something different to scale appropriately.
    """

    from numpy import median
    import images

    ims *= (scale*nominal_exptime/exptime)

    ims = images.asinh_scale(ims, nonlinear)
    return ims

def write_jpg(fname, im, **keys):
    """
    image is flipped up-down and transposed so that, in a jpg, north is up and
    east is left.  The image is bytescaled, so should be between [0,1].

    extra keywords for images.write_image() are passed on.
    """
    from numpy import flipud
    import images

    # for DES images this results in north up east to the left
    # because jpg coordinates start in the upper left
    imout = flipud(im)
    imout=imout.transpose()

    imout = images.bytescale(imout)
    images.write_image(fname, imout, **keys)

    return imout.shape



