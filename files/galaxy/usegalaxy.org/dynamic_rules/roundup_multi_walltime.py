##
## This file is maintained by Ansible - CHANGES WILL BE OVERWRITTEN
##

import logging
import datetime
from galaxy.jobs.mapper import JobMappingException

log = logging.getLogger(__name__)

ROUNDUP_DESTINATION = 'roundup_multi'
ROUNDUP_DEVELOPMENT_DESTINATION = 'roundup_single_development'
STAMPEDE_DESTINATION = 'pulsar_stampede'
STAMPEDE_DEVELOPMENT_DESTINATION = 'pulsar_stampede_development'
STAMPEDE_DESTINATIONS = (STAMPEDE_DESTINATION, STAMPEDE_DEVELOPMENT_DESTINATION)
VALID_DESTINATIONS = STAMPEDE_DESTINATIONS + (ROUNDUP_DESTINATION, ROUNDUP_DEVELOPMENT_DESTINATION) # WHY ARE WE SHOUTING
RESOURCE_KEYS = ('tacc_compute_resource', 'stampede_compute_resource')
FAILURE_MESSAGE = 'This tool could not be run because of a misconfiguration in the Galaxy job running system, please report this error'

# in minutes
RUNTIMES = {
    'bowtie_wrapper': {'runtime': 19.75, 'stddev': 65.27},
    'bwa_wrapper': {'runtime': 51.47, 'stddev': 157.78},
    'bowtie2': {'runtime': 28.23, 'stddev': 45.48},
    'cuffdiff': {'runtime': 108.27, 'stddev': 258.30},
    'tophat': {'runtime': 152.69, 'stddev': 295.26},
    'tophat2': {'runtime': 165.47, 'stddev': 286.19},
    'cufflinks': {'runtime': 44.73, 'stddev': 157.20},
    'cuffmerge': {'runtime': 35.07, 'stddev': 181.65}
}
DEVS = 2

def roundup_multi_dynamic_walltime( app, tool, job, user_email ):
    destination = None
    destination_id = ROUNDUP_DESTINATION

    if user_email is None:
        raise JobMappingException( 'Please log in to use this tool.' )

    param_dict = dict( [ ( p.name, p.value ) for p in job.parameters ] )
    param_dict = tool.params_from_strings( param_dict, app )
    
    # Explcitly set the destination if the user has chosen to do so with the resource selector
    if '__job_resource' in param_dict and param_dict['__job_resource']['__job_resource__select'] == 'yes':
        resource_key = None
        for resource_key in param_dict['__job_resource'].keys():
            if resource_key in RESOURCE_KEYS:
                break
        else:
            log.warning('(%s) Stampede dynamic plugin did not find a valid resource key, keys were: %s', job.id, param_dict['__job_resource'].keys())
            raise JobMappingException( FAILURE_MESSAGE )

        destination_id = param_dict['__job_resource'][resource_key]
        if destination_id not in VALID_DESTINATIONS:
            log.warning('(%s) Stampede dynamic plugin got an invalid destination: %s', job.id, destination_id)
            raise JobMappingException( FAILURE_MESSAGE )

    # Set a walltime if the roundup_multi is the destination
    if destination_id == ROUNDUP_DESTINATION:
        tool_id = tool.id.split('/')[-2]
        if tool_id not in RUNTIMES:
            log.error('(%s) Invalid tool for this dynamic rule: %s', job.id, tool_id)
            raise JobMappingException( FAILURE_MESSAGE )

        walltime = datetime.timedelta(seconds=(RUNTIMES[tool_id]['runtime'] + (RUNTIMES[tool_id]['stddev'] * DEVS)) * 60)
        destination = app.job_config.get_destination( ROUNDUP_DESTINATION ) 
        destination.params['nativeSpecification'] += ' --time=%s' % str(walltime).split('.')[0]

    log.debug("(%s) slurm_multi_dynamic_walltime dynamic plugin returning '%s' destination", job.id, destination_id)
    if destination is not None and 'nativeSpecification' in destination.params:
        log.debug("     nativeSpecification is: %s", destination.params['nativeSpecification'])
    return destination or destination_id