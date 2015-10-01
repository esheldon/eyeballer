from __future__ import print_function
import os

import desdb


def get_dir():
    """
    Get the main directory
    """
    return os.environ['EYEBALLER_DATADIR']

def get_run_dir(run):
    """
    The base run directory

    parameters
    ----------
    run: string
        the run identifier
    """
    return os.path.join(get_dir(), run)

def get_script_dir(run):
    """
    The script directory

    parameters
    ----------
    run: string
        the run identifier
    """
    rd=get_run_dir(run)
    return os.path.join(rd, 'scripts')

def get_master_file(run):
    """
    The script directory

    parameters
    ----------
    run: string
        the run identifier
    """
    sd=get_script_dir(run)
    return os.path.join(sd, 'master.sh')

def get_command_file(run, num, missing=False):
    """
    The command file

    parameters
    ----------
    run: string
        the run identifier
    missing: bool
        For missing files
    """
    sd=get_script_dir(run)
    if missing:
        fname='commands-missing-%06d.sh' % num
    else:
        fname='commands-%06d.sh' % num
    return os.path.join(sd, fname)


def get_wq_file(run, num, missing=False):
    """
    The script directory

    parameters
    ----------
    run: string
        the run identifier
    missing: bool
        For missing files
    """
    sd=get_script_dir(run)
    if missing:
        fname='sub-missing-%06d.yaml' % num
    else:
        fname='sub-%06d.yaml' % num
    return os.path.join(sd, fname)


def get_output_file(run,
                    reqnum,
                    expnum,
                    attnum,
                    ccdnum,
                    band,
                    df=None):
    """
    The output directory

    parameters
    ----------
    run: string
        the run identifier
    """
    if df is None:
        df=desdb.files.DESFiles()

    imfile=df.url(type='red_immask',
                  reqnum=reqnum,
                  expnum=expnum,
                  attnum=attnum,
                  ccdnum=ccdnum,
                  band=band)
    
    rundir=get_run_dir(run)
    desdata=os.environ['DESDATA']
    fname=imfile.replace(desdata,rundir)

    fname=fname.replace('.fits.fz','.fits').replace('.fits','-eyeball.fits.fz')
    return fname



def get_output_dir_runexpnum(run, expname):
    """
    The output directory

    parameters
    ----------
    run: string
        the run identifier
    expname: string
        the exposurename
    """
    rd=get_run_dir(run)
    return os.path.join(rd, expname)


def get_output_file_runexpccd(run, expname, ccd):
    """
    Output file location

    parameters
    ----------
    run: string
        the run identifier
    expname: string
        the exposurename
    """
    d=get_output_dir(run, expname)
    fname='%(run)s_%(expname)s_%(ccd)02d_field.fits.fz'
    fname = fname % {'run':run,
                     'expname':expname,
                     'ccd':ccd}
    path=os.path.join(d, fname)
    return path

def get_config_dir():
    """
    Get the config directory from the github
    """

    d=os.environ['EYEBALLER_DIR']
    return os.path.join(d, 'share', 'eyeball-config')

def get_config_file(run):
    """
    Get the config file path

    parameters
    ----------
    run: string
        the run identifier
    """ 

    d=get_config_dir()
    fname='%s.yaml' % run
    return os.path.join(d, fname)

def read_config(run):
    """
    read the config file

    parameters
    ----------
    run: string
        the run identifier
    """ 
    import yaml
    path=get_config_file(run)

    with open(path) as fobj:
        conf=yaml.load(fobj)

    return conf

def get_db_dir(run):
    """
    The database directory

    parameters
    ----------
    run: string
        the run identifier
    """
    rd=get_run_dir(run)
    return os.path.join(rd, 'db')

def get_db_file(run):
    """
    The db file path

    parameters
    ----------
    run: string
        the run identifier
    """
    dd=get_db_dir(run)
    fname='%s.db' % run
    return os.path.join(dd, fname)


def load_run_explist(fname):
    """
    load a three-column file with run, expname, band

    parameters
    ----------
    fname: string
        The path to the file

    output
    ------
    list of dicts holding run and expname
    """
    run_explist=[]
    print("loading run,exp from:",fname)
    with open(fname) as fobj:
        for line in fobj:
            ls=line.split()

            run_explist.append( {'run':ls[0], 'expname':ls[1], 'band':ls[2]} )

    return run_explist


#
# outputs from any weak lensing pipeline
#

'''
# se exp names have underscores so we use underscores
_fs1['wlpipe'] = {'dir': '$DESDATA/wlpipe'}
_fs1['wlpipe_run'] = {'dir': _fs1['wlpipe']['dir']+'/$RUN'}

_fs1['wlpipe_collated'] = {'dir':_fs1['wlpipe_run']['dir']+'/collated'}
_fs1['wlpipe_collated_goodlist'] = {'dir':_fs1['wlpipe_collated']['dir'],
                                   'name':'$RUN-goodlist.json'}
_fs1['wlpipe_collated_badlist'] = {'dir':_fs1['wlpipe_collated']['dir'],
                                  'name':'$RUN-badlist.json'}



_fs1['wlpipe_pbs']    = {'dir': _fs1['wlpipe_run']['dir']+'/pbs'}
_fs1['wlpipe_condor'] = {'dir': _fs1['wlpipe_run']['dir']+'/condor'}

_fs1['wlpipe_scratch'] = {'dir': '$TMPDIR/DES/wlpipe'}
_fs1['wlpipe_scratch_run'] = {'dir': _fs1['wlpipe_scratch']['dir']+'/$RUN'}
#_fs1['wlpipe_pbs'] = {'dir': _fs1['wlpipe_scratch_run']['dir']+'/pbs'}

_fs1['wlpipe_flists'] = {'dir': _fs1['wlpipe_run']['dir']+'/flists'}
_fs1['wlpipe_flist_red'] = {'dir': _fs1['wlpipe_flists']['dir'],
                           'name':'$RUN_red_info.json'}


# SE files by exposure name
_fs1['wlpipe_exp'] = {'dir': _fs1['wlpipe_run']['dir']+'/$EXPNAME'}

# generic, for user use
_fs1['wlpipe_se_generic'] = {'dir': _fs1['wlpipe_exp']['dir'],
                            'name': '$RUN_$EXPNAME_$CCD_$FILETYPE.$EXT'}


# required
# meta has inputs, outputs, other metadata
_fs1['wlpipe_se_meta'] = {'dir': _fs1['wlpipe_exp']['dir'],
                         'name': '$RUN_$EXPNAME_$CCD_meta.json'}
_fs1['wlpipe_se_status'] = {'dir': _fs1['wlpipe_exp']['dir'],
                           'name': '$RUN_$EXPNAME_$CCD_status.txt'}

# scripts are also pbs scripts
_fs1['wlpipe_se_script'] = \
    {'dir': _fs1['wlpipe_pbs']['dir']+'/byexp/$EXPNAME',
     'name': '$EXPNAME_$CCD_script.pbs'}
_fs1['wlpipe_se_check'] = \
    {'dir': _fs1['wlpipe_pbs']['dir']+'/byexp/$EXPNAME',
     'name': '$EXPNAME_$CCD_check.pbs'}
_fs1['wlpipe_se_log'] = \
    {'dir': _fs1['wlpipe_pbs']['dir']+'/byexp/$EXPNAME',
     'name': '$EXPNAME_$CCD_script.log'}


# ME files by tilename and band
# tile names have dashes so we use dashes
_fs1['wlpipe_tile'] = {'dir': _fs1['wlpipe_run']['dir']+'/$TILENAME'}
_fs1['wlpipe_scratch_tile'] = {'dir': _fs1['wlpipe_scratch_run']['dir']+'/$TILENAME'}

# non-split versions
_fs1['wlpipe_me_generic'] = {'dir': _fs1['wlpipe_tile']['dir'],
                            'name': '$RUN-$TILENAME-$FILETYPE.$EXT'}

#_fs1['wlpipe_me_meta'] = {'dir': _fs1['wlpipe_tile']['dir'],
#                         'name': '$RUN-$TILENAME-meta.json'}
_fs1['wlpipe_me_meta'] = {'dir': _fs1['wlpipe_scratch_tile']['dir'],
                         'name': '$RUN-$TILENAME-meta.json'}
_fs1['wlpipe_me_status'] = {'dir': _fs1['wlpipe_tile']['dir'],
                           'name': '$RUN-$TILENAME-status.txt'}

# ME split versions
_fs1['wlpipe_me_split'] = \
    {'dir': _fs1['wlpipe_tile']['dir'],
     'name': '$RUN-$TILENAME-$START-$END-$FILETYPE.$EXT'}

_fs1['wlpipe_me_collated'] = {'dir':_fs1['wlpipe_collated']['dir'],
                             'name':'$RUN-$TILENAME-$FILETYPE-collated.$EXT'}
_fs1['wlpipe_me_collated_blinded'] = {'dir':_fs1['wlpipe_collated']['dir'],
                                     'name':'$RUN-$TILENAME-$FILETYPE-collated-blind.$EXT'}
_fs1['wlpipe_me_download'] = {'dir':_fs1['wlpipe_collated']['dir'],
                             'name':'download.html'}


_fs1['wlpipe_me_meta_split'] = \
    {'dir': _fs1['wlpipe_scratch_tile']['dir'],
     'name': '$RUN-$TILENAME-$START-$END-meta.json'}
_fs1['wlpipe_me_status_split'] = \
    {'dir': _fs1['wlpipe_tile']['dir'],
     'name': '$RUN-$TILENAME-$START-$END-status.txt'}

# these names are independent of me or se
_fs1['wlpipe_master_script'] =  {'dir': _fs1['wlpipe_condor']['dir'], 'name': 'master.sh'}
_fs1['wlpipe_commands'] = {'dir': _fs1['wlpipe_condor']['dir'], 'name': 'commands.txt'}



_fs1['wlpipe_me_tile_commands'] = {'dir': _fs1['wlpipe_pbs']['dir'],
                                  'name': '$TILENAME-commands.txt'}
_fs1['wlpipe_me_tile_minions'] = {'dir': _fs1['wlpipe_pbs']['dir'],
                                 'name': '$TILENAME-minions.pbs'}


# condor
# different clusters per tile.
_fs1['wlpipe_me_tile_condor'] = \
    {'dir': _fs1['wlpipe_condor']['dir']+'/submit',
     'name': '$TILENAME.condor'}
_fs1['wlpipe_me_tile_condor_missing'] = \
    {'dir': _fs1['wlpipe_condor']['dir']+'/submit',
     'name': '$TILENAME-missing.condor'}


_fs1['wlpipe_me_tile_checker'] = {'dir': _fs1['wlpipe_condor']['dir']+'/check',
                                 'name': '$TILENAME-check.sh'}

# all in one cluster
_fs1['wlpipe_me_condor'] = {'dir': _fs1['wlpipe_condor']['dir'],
                           'name': '$RUN.condor'}
_fs1['wlpipe_me_condor_missing'] = {'dir': _fs1['wlpipe_condor']['dir'],
                                   'name': '$RUN-missing.condor'}


_fs1['wlpipe_me_checker'] = {'dir': _fs1['wlpipe_condor']['dir'],
                            'name': '$RUN-check.sh'}

_fs1['wlpipe_me_log_split'] = \
    {'dir': _fs1['wlpipe_condor']['dir']+'/logs/$TILENAME',
     'name': '$TILENAME-$START-$END.log'}



_fs1['wlpipe_me_script_split'] = \
    {'dir': _fs1['wlpipe_pbs']['dir']+'/bytile/$TILENAME',
     'name': '$TILENAME-$START-$END-script.pbs'}
_fs1['wlpipe_me_check_split'] = \
    {'dir': _fs1['wlpipe_pbs']['dir']+'/bytile/$TILENAME',
     'name': '$TILENAME-$START-$END-check.pbs'}



_fs1['wlpipe_minions'] = {'dir': _fs1['wlpipe_pbs']['dir'], 'name': 'minions.pbs'}
_fs1['wlpipe_minions_check'] = {'dir': _fs1['wlpipe_pbs']['dir'],
                               'name': 'check-minions.pbs'}
_fs1['wlpipe_check_reduce'] = {'dir': _fs1['wlpipe_pbs']['dir'],
                              'name': 'reduce-check.py'}


'''
