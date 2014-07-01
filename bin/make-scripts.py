"""
    %prog [options] run-name
"""
from __future__ import print_function
import sys, os
from optparse import OptionParser
import desdb
import eyeballer

parser=OptionParser(__doc__)

parser.add_option('--chunksize', default=300,
                  help="number of jobs per submit file")


def get_master_script():
    text="""#!/bin/bash

# assuming the environment is empty, as in a wq job
source ~/shell_scripts/eyeball-prepare.sh

image="$1"
bkg="$2"
field_fits="$3"

if [[ -e $field_fits ]]; then
    echo "file exists, skipping"
    exit 0
fi

bname=$(basename $field_fits)
dname=$(dirname $field_fits)

mkdir -p ${dname}
mkdir -p /data/esheldon/tmp
tmpname=/data/esheldon/tmp/${bname}

python $EYEBALLER_DIR/bin/make-se-eyeball.py ${image} ${bkg} ${tmpname}
exit_status=$?

if [[ -e ${tmpname} ]]; then
    mv -v ${tmpname} ${field_fits}
else
    echo "file is missing: ${tmpname}"
fi

exit $exit_status\n"""

    return text


def load_run_explist(fname):
    runlist=[]
    explist=[]
    with open(fname) as fobj:
        for line in fobj:
            ls=line.split()
            runlist.append(ls[0])
            explist.append(ls[1])

    return runlist, explist

def write_master(run):
    url=eyeballer.files.get_master_file(run)
    d=os.path.dirname(url)
    if not os.path.exists(d):
        os.makedirs(d)

    print("writing master:",url)
    with open(url,'w') as fobj:
        text=get_master_script()
        fobj.write(text)

    cmd='chmod 755 '+url
    print(cmd)
    os.system(cmd)

def main():
    options, args = parser.parse_args(sys.argv[1:])

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    run=args[0]
    chunksize=int(options.chunksize)

    conf=eyeballer.files.read_config(run)

    write_master(run)

    runlist, explist = load_run_explist(conf['run_explist'])

    conn=desdb.Connection()

    desdata=desdb.files.get_des_rootdir()
    skip_ccds=desdb.files.SKIP_CCDS_CSV

    num=0

    for run,exp in zip(runlist,explist):
        query="""
        select
            '%(desdata)s/' || loc.project || '/red/' || image.run || '/red/' || loc.exposurename || '/' || image.imagename || '.fz' as image_url,
            loc.exposurename as expname,
            loc.band,
            image.ccd,
            image.id as image_id,
            image.run as red_run
        from
            image, location loc
        where
            image.run = '%(run)s'
            and loc.exposurename = '%(expname)s'
            and loc.id=image.id
            and image.imagetype='red'
            and image.ccd not in (%(skip_ccds)s)
        """

        query=query % {'run':run,
                       'expname':exp,
                       'desdata':desdata,
                       'skip_ccds':skip_ccds}

        # list of dicts
        data=conn.quick(query)

        for r in data:
            bkg_url=r['image_url'].replace('.fits.fz','_bkg.fits.fz')
            print(r['red_run'],r['expname'],r['ccd'])


main()
