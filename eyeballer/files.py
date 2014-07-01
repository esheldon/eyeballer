import os

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

def get_command_file(run, num):
    """
    The command file

    parameters
    ----------
    run: string
        the run identifier
    """
    sd=get_script_dir(run)
    return os.path.join(sd, 'commands-%06d.sh' % num)


def get_wq_file(run, num):
    """
    The script directory

    parameters
    ----------
    run: string
        the run identifier
    """
    sd=get_script_dir(run)
    fname='sub-%06d.yaml' % num
    return os.path.join(sd, fname)


def get_output_dir(run, expname):
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

def get_output_file(run, expname, ccd):
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
