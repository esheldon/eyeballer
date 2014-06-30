eyeballer
==========

Make cutouts for eyeballing from an image and catalog

Cutout file format
------------------

- First extension is "metadata", which is a table with the input filenames,
   requested cutout size, number of cutouts, etc.

- Second extension is "centers", which describes the centers used to make the
  cutouts.   One row per center, listing index in the original catalog, center
  row and center column (zero offset).

- Third extension is "mosaic" holds the mosaic of cutouts.  This will
  be square, so 100 cutouts will be in a 10x10 grid.

Dependencies
------------
- numpy
- fitsio https://github.com/esheldon/fitsio
