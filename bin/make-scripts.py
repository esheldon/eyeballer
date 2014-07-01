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

    run_explist=[]
    with open(fname) as fobj:
        for line in fobj:
            ls=line.split()

            run_explist.append( {'run':ls[0], 'expname':ls[1]} )

    return run_explist

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

def get_command_template():
    """
    note indent
    """
    t="""echo %(expname)s %(ccd)s
./master.sh %(image)s %(bkg)s %(field_fits)s &> %(log)s\n"""
    return t

def open_command_file(eye_run, num):
    fname=eyeballer.files.get_command_file(eye_run, num)
    print("opening command file:",fname)

    fobj=open(fname,'w')
    return fobj

def write_wq_script(eye_run, num):
    wq_file=eyeballer.files.get_wq_file(eye_run, num)
    comfile=eyeballer.files.get_command_file(eye_run, num)
    comfile=os.path.basename(comfile)

    print("writing wq script:",wq_file)
    with open(wq_file,'w') as fobj:
        job_name='%s-%06d' % (eye_run, num)
        text="""
job_name: "{job_name}"

command: |
    source ~/shell_scripts/eyeball-prepare.sh
    bash {comfile}
        \n""".format(job_name=job_name,
                     comfile=comfile)
        fobj.write(text)

def make_output_dir(eye_run, expname):
    d=eyeballer.files.get_output_dir(eye_run, expname)
    if not os.path.exists(d):
        print("making dir:",d)
        os.makedirs(d)

def main():
    options, args = parser.parse_args(sys.argv[1:])

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    eye_run=args[0]
    chunksize=int(options.chunksize)

    conf=eyeballer.files.read_config(eye_run)

    write_master(eye_run)

    run_explist = load_run_explist(conf['run_explist'])
    ntot=len(run_explist)

    conn=desdb.Connection()

    desdata=desdb.files.get_des_rootdir()
    skip_ccds=desdb.files.SKIP_CCDS_CSV

    command_template=get_command_template()

    num=0
    i=0
    for idict,rdict in enumerate(run_explist):

        make_output_dir(eye_run, rdict['expname'])

        print("%d/%d %s" % (idict+1,ntot,rdict['expname']))
        query="""
        select
            '%(desdata)s/' || loc.project || '/red/' || image.run || '/red/' || loc.exposurename || '/' || image.imagename || '.fz' as image,
            loc.exposurename as expname,
            loc.band,
            image.ccd,
            image.id as image_id,
            image.run as run
        from
            image, location loc
        where
            image.run = '%(run)s'
            and loc.exposurename = '%(expname)s'
            and loc.id=image.id
            and image.imagetype='red'
            and image.ccd not in (%(skip_ccds)s)
        """

        query=query % {'run':rdict['run'],
                       'expname':rdict['expname'],
                       'desdata':desdata,
                       'skip_ccds':skip_ccds}

        # list of dicts
        data=conn.quick(query)

        for r in data:

            if (i % chunksize) == 0:
                write_wq_script(eye_run, num)
                if num != 0:
                    fobj.close()

                fobj=open_command_file(eye_run, num)
                fobj.write('#!/bin/bash\n')
                num += 1

            r['bkg']        = r['image'].replace('.fits.fz','_bkg.fits.fz')
            r['field_fits'] = eyeballer.files.get_output_file(eye_run,r['expname'],r['ccd'])
            r['log']        = r['field_fits'].replace('.fits.fz','.log')

            ok=True
            if not os.path.exists(r['image']):
                print("error: missing image:",r['image'])
                ok=False
            if not os.path.exists(r['bkg']):
                print("error: missing bkg:",r['bkg'])
                ok=False

            if ok:
                command = command_template % r
                print(command, file=fobj)
                i+=1


main()
