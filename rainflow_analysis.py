''' This scripts executes a generic rainflow analysis '''

# It's going to have basically call 3 functions

# Through parameter or initi file (probably better the latter)


# Call the getpop with the proper parameters


# Call execute rainfloww with the proper parametees


''' TO DO :
- add the parameter to reas the input config file
- double check if we have the same results for the rainflow
- Ideally I may want to generalize this to dump a big dataframe of sig data 
	but it doesnt' seem to be a usecase we want or need
- Add the check for creating output directories if they don't exists

'''
from relpy import popBox as pb
from relpy import procBox as pcb
from relpy import statBox as sb
from relpy import utils as ut
import pandas as pd
import sys, getopt
import time
import json

# Shall globals be in the configuration file probably not

# Here read the parameters and call the pb accordingly
# The only parameter here should be the config file name


# Here get the config file path from the command line as parameter
if len(sys.argv)<2:
		print("Usage: %s -c config_file" % sys.argv[0])
		sys.exit(2)
else:
	try:
		myopts, args = getopt.getopt(sys.argv[1:],"c:")
	except getopt.GetoptError as e:
		print (str(e))
		print("Usage: %s -c config_file" % sys.argv[0])
		sys.exit(2)

	for o, a in myopts:
		if o == '-c':
			config_file=a
		    

# config_file = "./extended_rainflow/input/config/rainflow_analysis_config_test_2.json"

config = json.loads(open(config_file, 'r').read())
print config

# Creates a dicitonary to 
# store all rifmatrix
rif_matrix_dict = dict()
# Intialilzes the vector to store the sum of all the computed rif matrices
sum_out_vector = []
norm_out_vector = []
sig_df_vect = []

# Initialize the result dict
results = dict()
count = 0

print "Starting execution..."

# Creates Dirs
ut.create_dir(path = config["out_dir"], dirDict = dict(csv = None, pickle = None, figures = None,
	config = None, dataframes = None, distributions = None, output_vectors = None, dicts = None ))

### GET POP DATA ####

if not config["skip_pop"]:
	print "Pop found"
	pop_df = pb.computepop(customer_carsTF = config["pop_params"]["customer_carsTF"], master_value = config["pop_params"]["master_value"], runOdom = config["pop_params"]["runOdom"], 
		num_samples=config["pop_params"]["num_samples"], days_in_field=config["pop_params"]["days_in_field"], region_value=config["pop_params"]["region_value"], 
	    subregion_value=config["pop_params"]["subregion_value"],country_value=config["pop_params"]["country_value"], min_warranty_date=config["pop_params"]["min_warranty_date"])


else:
	if config["pop_pickle"] is not None:
		pop_df = ut.readpickle(config["pop_pickle"])
	else:
		print " Need to provide a pickled dataframe or execute a pop query"
		exit(0)
	# Try to read the df or the pickle
	# Here I need to generalized the compute_rainflow to accept directly 

### GET SIGNAL DATA ####

# Here vehilce id is kind of hard coded
# FIne for now but need to take care of it

# If I provide the pickle I need to call the compute rainflow just one time

if config["skip_signal"] is False:

	for vid in pop_df.vehicle_id:
		count +=1
		print vid
		print "Processing vehicle %d out of %d" %(count, len(pop_df.vehicle_id.unique()) )

		# Here I don't jave to retrieve the signal If I provide a matrix
		sig_df  = pcb.retrieveSignal(sigTbl = config["sig_params"]['sigTbl'], 
			sigId = config["sig_params"]['sigId'],vid = int(vid), 
			master = config["sig_params"]["master"], queryName = "sig_valueQuery", 
			where= config["sig_params"]["where"],sign= config["sig_params"]["sign"], 
			days_back=config["sig_params"]["days_back"])

		# Just for testing to be removed 
		if config["save_signal"]:
			sig_df_vect.append(sig_df)
		# print sig_df.shape
		# print sig_df.head()

		### APPLY RAINFLOW ####

		# Here need to tweak the compute rainflow not to save the actual data
		rif_matrix, norm_matrix, computed_matrix = pcb.computeRainFlow(measurement_column = config["rainflow_params"]["measurement_column"],
		unique_elem_column = config["rainflow_params"]["unique_elem_column"], dtt = config["rainflow_params"]["dtt"],
		g =config["rainflow_params"]["g"], min_val= config["rainflow_params"]["min_val"], max_val = config["rainflow_params"]["max_val"],
		step = config["rainflow_params"]["step"], df = sig_df, num_bins = config["rainflow_params"]["num_bins"], 
		save = config["rainflow_params"]["save"], verbose = config["rainflow_params"]["verbose"],
		plot = config["rainflow_params"]["plot"], out_dir = config["out_dir"], csv=config["rainflow_params"]["csv"])

		# Here's the problem it seems that norm_matrix and
		# Computed Matrix is the same
		#print norm_matrix
		#print computed_matrix
		

		# Append the computed matrix to the dict
		rif_matrix_dict[vid] = computed_matrix

		# Append the sum of the matrix to out vector
		sum_out_vector.append(sum(computed_matrix.sum()))

		# Here I want to get the su of normalized matrix
		norm_out_vector.append(sum(norm_matrix.sum()))

else:
	# Here handle the case when I have a pickle file
	# IN this case I have the whole pickel files with different Ids 
	# just get the signal data
	# Just computing the rainflow

	# Here calls the compute Rainflow with teh df as the pop df which has 
	# all the signal data already AND the skipped_signal = true
	print ("Here")
	rif_matrix, norm_matrix, computed_matrix, sum_out_vector, norm_out_vector,  rif_matrix_dict = pcb.computeRainFlow(measurement_column = config["rainflow_params"]["measurement_column"],
		unique_elem_column = config["rainflow_params"]["unique_elem_column"], dtt = config["rainflow_params"]["dtt"],
		g = config["rainflow_params"]["g"], min_val= config["rainflow_params"]["min_val"], max_val = config["rainflow_params"]["max_val"],
		step = config["rainflow_params"]["step"], df = pop_df, num_bins = config["rainflow_params"]["num_bins"], 
		save = config["rainflow_params"]["save"], verbose = config["rainflow_params"]["verbose"],
		plot = config["rainflow_params"]["plot"], out_dir = config["out_dir"], csv=config["rainflow_params"]["csv"], 
		skipped_pop=True, pkl=config["sig_pickle"])


# Fits distribution and compute results
my_dist = sb.dist(X=sum_out_vector)



results['dist_name']= my_dist.distName 
results['dist_params'] = my_dist.theta
results['95th_perc'] = my_dist.rv.ppf(0.95)
results['out_vector'] =  sum_out_vector


# Here I'm trying to fit the distribution to the norm_outv_vector
# But is oddily the same as the other stuff.
# Need to debug
# field_cycle_dist = sb.dist(X=norm_out_vector)
# results['field_cycle_dist_name']= field_cycle_dist.distName 
# results['field_cycle_dist_params'] = field_cycle_dist.theta
# results['field_cycle_95th_perc'] = field_cycle_dist.rv.ppf(0.95)
# results['field_cycle_out_vector'] =  norm_out_vector

# Prints results
for k,v in results.iteritems():
	print k , v
	

### STORE ANALYSIS RESULTS ####

if config["save"]:
    timestamp = time.time()
    # I want to pickle the pop matrix and save it in the input folder
    ut.savepickle(pop_df, config["out_dir"]+"pickle/pop_df_"+str(timestamp)+".pkl")
    # Here I'm merging the signal matrices and save them as input
    if config["save_signal"]:
	    merged_vect = pd.concat(sig_df_vect) 
	    ut.savepickle(merged_vect, config["out_dir"]+"pickle/signal_df"+str(timestamp)+".pkl")
    
    my_dist.save_dist(config["out_dir"]+"distributions/rainflow_dist_"+str(timestamp)+".pkl")
   
    #field_cycle_dist.save_dist(config["out_dir"]+"distributions/Field_cycle_dist_"+str(timestamp)+".pkl")
    
    ut.savepickle(rif_matrix_dict, config["out_dir"]+"dicts/rainflow_matrix_vector_"+str(timestamp)+".pkl")
    ut.savepickle(results, config["out_dir"]+"output_vectors/results_"+str(timestamp)+".pkl")
    # Saves the dist plot 
    my_dist.plot(saveAs = config["out_dir"]+"figures/"+my_dist.distName+"_dist_plot_"+str(timestamp)+".png")    
    
    #field_cycle_dist.plot(saveAs = config["out_dir"]+"figures/"+"field_cycle_"+field_cycle_dist.distName+"_dist_plot_"+str(timestamp)+".png")    
   

    # Store the config jason with time stamp
    with open(config["out_dir"]+"config/"+'config_file_'+str(timestamp)+'.json', 'w') as outfile:
    	json.dump(config, outfile)
