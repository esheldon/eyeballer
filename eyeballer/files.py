import os

def get_dir():
    """
    Get the main directory
    """
    return os.environ['EYEBALL_DATADIR']

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
    fname='eye_%(run)s_%(expname)s_%(ccd)02d_field.fits.fz'
    fname = fname % {'run':run,
                     'expname':expname,
                     'ccd':ccd}
    path=os.path.join(d, path)
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
    fname='eyeball-%s.yaml' % run
    return os.path.join(d, fname)

