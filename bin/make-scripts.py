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
parser.add_option('--missing', action='store_true',
                  help="only create scripts for missing files")



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
./master.sh %(image_url)s %(bkg)s %(field_fits)s &> %(log)s\n"""
    return t

def open_command_file(eye_run, num, missing=False):
    fname=eyeballer.files.get_command_file(eye_run, num, missing=missing)
    print("opening command file:",fname)

    fobj=open(fname,'w')
    return fobj

def write_wq_script(eye_run, num, missing=False):
    wq_file=eyeballer.files.get_wq_file(eye_run, num, missing=missing)
    comfile=eyeballer.files.get_command_file(eye_run, num, missing=missing)
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

    run_explist = eyeballer.files.load_run_explist(conf['run_explist'])
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

        data = desdb.files.get_red_info_by_run(rdict['run'],
                                               expname=rdict['expname'],
                                               conn=conn)

        for r in data:
            r['bkg']        = r['image_url'].replace('.fits.fz','_bkg.fits.fz')
            r['field_fits'] = eyeballer.files.get_output_file(eye_run,r['expname'],r['ccd'])
            r['log']        = r['field_fits'].replace('.fits.fz','.log')

            if options.missing and os.path.exists(r['field_fits']):
                continue

            if (i % chunksize) == 0:
                write_wq_script(eye_run, num, missing=options.missing)
                if num != 0:
                    fobj.close()

                fobj=open_command_file(eye_run, num, missing=options.missing)
                fobj.write('#!/bin/bash\n')
                num += 1

            ok=True
            if not os.path.exists(r['image_url']):
                print("error: missing image:",r['image_url'])
                ok=False
            if not os.path.exists(r['bkg']):
                print("error: missing bkg:",r['bkg'])
                ok=False

            if ok:
                command = command_template % r
                print(command, file=fobj)
                i+=1


main()
