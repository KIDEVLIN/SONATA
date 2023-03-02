import os
import time
import numpy as np
import matplotlib.pyplot as plt
from SONATA.classBlade import Blade
from SONATA.utl.beam_struct_eval import beam_struct_eval
from SONATA.utl_openfast.utl_run_fast import utl_run_fast

# Path to yaml file
run_dir = os.path.dirname( os.path.realpath(__file__) ) + os.sep
job_str = 'IEA-15-240-RWT.yaml'
job_name = 'IEA15'
filename_str = run_dir + job_str

# ===== Define flags ===== #
flag_wt_ontology        = True # if true, use ontology definition of wind turbines for yaml files
flag_ref_axes_wt        = True # if true, rotate reference axes from wind definition to comply with SONATA (rotorcraft # definition)

# --- plotting flags ---
# Define mesh resolution, i.e. the number of points along the profile that is used for out-to-inboard meshing of a 2D blade cross section
mesh_resolution = 400
# For plots within blade_plot_sections
attribute_str           = 'MatID'  # default: 'MatID' (theta_3 - fiber orientation angle)
                                            # others:  'theta_3' - fiber orientation angle
                                            #          'stress.sigma11' (use sigma_ij to address specific component)
                                            #          'stressM.sigma11'
                                            #          'strain.epsilon11' (use epsilon_ij to address specific component)
                                            #          'strainM.epsilon11'

# 2D cross sectional plots (blade_plot_sections)
flag_plotTheta11        = False      # plane orientation angle
flag_recovery           = False
flag_plotDisplacement   = True     # Needs recovery flag to be activated - shows displacements from loadings in cross sectional plots
# 3D plots (blade_post_3dtopo)
flag_wf                 = True      # plot wire-frame
flag_lft                = True      # plot lofted shape of blade surface (flag_wf=True obligatory); Note: create loft with grid refinement without too many radial_stations; can also export step file of lofted shape
flag_topo               = True      # plot mesh topology
c2_axis                 = True
rm_vabfiles             = False     # Remove or keep VABS input files once generated. It is possible to set the flag to True even without a valid installation of VABS


# create flag dictionary
flags_dict = {"flag_wt_ontology": flag_wt_ontology, "flag_ref_axes_wt": flag_ref_axes_wt,
              "attribute_str": attribute_str,
              "flag_plotDisplacement": flag_plotDisplacement, "flag_plotTheta11": flag_plotTheta11,
              "flag_wf": flag_wf, "flag_lft": flag_lft, "flag_topo": flag_topo, "mesh_resolution": mesh_resolution,
              "flag_recovery": flag_recovery, "c2_axis": c2_axis, "rm_vabfiles": rm_vabfiles}


# ===== User defined radial stations ===== #
# Define the radial stations for cross sectional analysis (only used for flag_wt_ontology = True -> otherwise, sections from yaml file are used!)
# radial_stations = [0.  , 0.05, 0.1 ,   0.15, 0.2 , 0.25, 0.3 , 0.35, 0.4, 0.45, 0.5 , 0.55, 0.6 , 0.65, 0.7 , 0.75, 0.8 , 0.85, 0.9 , 0.95, 1.]
radial_stations = [0.3]

# ===== Execute SONATA Blade Component Object ===== #
# name          - job name of current task
# filename      - string combining the defined folder directory and the job name
# flags         - communicates flag dictionary (defined above)
# stations      - input of radial stations for cross sectional analysis
# stations_sine - input of radial stations for refinement (only and automatically applied when lofing flag flag_lft = True)
job = Blade(name=job_name, filename=filename_str, flags=flags_dict, stations=radial_stations)  # initialize job with respective yaml input file

# ===== Build & mesh segments ===== #
job.blade_gen_section(topo_flag=True, mesh_flag = True, split_quads=True)  # split_quads: vabs working with False & True; anbax working with True (only)

# ===== VABS / ANBAX combination/verification ===== #
# Define flags
flag_run_vabs = False
flag_run_anbax = True
flag_verify_vabs_anbax = False                  # needs flag_run_vabs & flag_run_anbax set to True to be valid!
flag_DeamDyn_def_transform = True               # transform from SONATA to BeamDyn coordinate system
flag_plot_vabs_struct_characteristics = False   # plots and saves figures of structural characteristics of respective analysis for the range of defined radial stations
flag_csv_export = False                          # export csv files with structural data
flag_write_BeamDyn = True                       # write BeamDyn input files for follow-up OpenFAST analysis (requires flag_DeamDyn_def_transform = True)
flag_write_BeamDyn_unit_convert = ''  #'mm_to_m'     # applied only when exported to BeamDyn files
# Update flags dictionary
flags_dict['flag_run_vabs'] = flag_run_vabs
flags_dict['flag_run_anbax'] = flag_run_anbax
flags_dict['flag_verify_vabs_anbax'] = flag_verify_vabs_anbax
flags_dict['flag_DeamDyn_def_transform'] = flag_DeamDyn_def_transform
flags_dict['flag_plot_vabs_struct_characteristics'] = flag_plot_vabs_struct_characteristics
flags_dict['flag_csv_export'] = flag_csv_export
flags_dict['flag_write_BeamDyn'] = flag_write_BeamDyn
flags_dict['flag_write_BeamDyn_unit_convert'] = flag_write_BeamDyn_unit_convert
Loads_dict = {}

# Set damping for BeamDyn input file
delta = np.array([0.03, 0.03, 0.06787]) # logarithmic decrement, natural log of the ratio of the amplitudes of any two successive peaks. 3% flap and edge, 6% torsion
zeta = 1. / np.sqrt(1.+(2.*np.pi / delta)**2.) # damping ratio,  dimensionless measure describing how oscillations in a system decay after a disturbance
omega = np.array([0.508286, 0.694685, 4.084712])*2*np.pi # Frequency (rad/s), flap/edge/torsion
mu1 = 2*zeta[0]/omega[0]
mu2 = 2*zeta[1]/omega[1]
mu3 = 2*zeta[2]/omega[2]
mu = np.array([mu1, mu2, mu3, mu2, mu1, mu3])
beam_struct_eval(flags_dict, Loads_dict, '', radial_stations, job, run_dir, job_str, mu)

# ===== PLOTS ===== #
# job.blade_plot_attributes()
# job.blade_plot_beam_props()

# saves figures in folder_str/figures if savepath is provided:
job.blade_plot_sections(attribute=attribute_str, plotTheta11=flag_plotTheta11, plotDisplacement=flag_plotDisplacement, savepath=run_dir)

job.blade_post_3dtopo(flag_wf=flags_dict['flag_wf'], flag_lft=flags_dict['flag_lft'], flag_topo=flags_dict['flag_topo'])

# # ===== RUN BeamDyn or OpenFAST ===== #
# utl_run_fast(BeamDyn_driver, FAST_driver, analysis_dir, input_file)  # ToDo upate path



