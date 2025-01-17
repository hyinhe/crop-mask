<img align="centre" src="../figs/Github_banner.jpg" width="101%">

#  Digital Earth Africa Continental Cropland Mask - Production

The code base here provides all the methods necessary for running the crop mask machine learning pipeline using AWS's [Kubernetes](https://kubernetes.io/) platform. The methods rely on the Open Data Cube's [Statistician](https://github.com/opendatacube/odc-stats) library for orchestrating the machine learning predicitions on AWS's cloud infrastructure. [Argo](https://argo.digitalearth.africa/workflows?limit=500) is used for deploying the code on kubernetes. [Argo](https://argoproj.github.io/workflows/) is a tool that simplifies orchestrating parallel job on kubernetes.

## How to build and install the crop-mask tools (`cm_tools`) library

In the folder `cm_tools/`, run the following shell command:

```bash
pip install cm_tools

```

## Local testing of production analysis code

The ODC-statistician plugin that does the core analysis can be tested within DE Africa's Sandbox environment using the notebook [1_test_plugin.ipynb](1_test_plugin.ipynb).

* The ODC-stats plugin is called [PredGMS2](cm_tools/cm_tools/gm_ml_pred.py)
* The two primary functions that this plugin references are in the [feature_layer](cm_tools/cm_tools/feature_layer.py) and [post_processing](cm_tools/cm_tools/post_processing.py) scripts.
* A yaml is required to configure the plugin, e.g. [config_western](cm_tools/cm_tools/config/config_western.yaml)

## List of Production Models for each AEZ

Within each testing folder a number of the earlier iteration models are retained. To reduce confusion, a list of the models used to create the production crop masks are listed below (these can also be found in the `Dockerfile`).  The date the training data and models were created identifies each iteration of model:

* Eastern: `testing/eastern_cropmask/results/gm_mads_two_seasons_ml_model_20210427.joblib`
* Western:  `testing/western_cropmask/results/western_ml_model_20210609.joblib`
* Northern: `testing/northern_cropmask/results/northern_ml_model_20210803.joblib`
* Sahel: `testing/sahel_cropmask/results/sahel_ml_model_20211110.joblib`
* Southern: `testing/southern_cropmask/results/southern_ml_model_20211108.joblib`
* South East: `testing/southeast_cropmask/results/southeast_ml_model_20220222.joblib`
* Central: `testing/central_cropmask/results/central_ml_model_20220304.joblib`

## Running production code
 
 > Note, the following contains an example of running the code on the production EKS, the workflow should first be tested in DEV-EKS.
 
        DEV Cluster: deafrica-dev-eks
        PROD Cluster: deafrica-prod-af-eks
 
The steps to create a large scale cropland extent map using K8s/Argo and the ML-methods described in this repo are as follows:

1. Ensure the `config_<region>` yaml is correct for the region of Africa you are running. i.e. one of these files [here](https://github.com/digitalearthafrica/crop-mask/tree/main/production/cm_tools/cm_tools/config)

2. Ensure the [Dockerfile](../Dockerfile) contains all the right files and libraries. If you alter the `Dockerfile` or the `cm_tools` code base you need to rebuild the image, this can triggered by changing the version number [here](../docker/version.txt) and creating a pull request.

3. Login to DE Africa's [Argo-production](https://argo.digitalearth.africa/workflows?limit=500) workspace (or [Argo-dev](https://argo.dev.digitalearth.africa/workflows?limit=500)), click on `submit workflow`, and use the drop-down box to select the `stats-crop-mask-processing` template.  The yaml file which creates this workflow is located [here](https://github.com/digitalearthafrica/datakube-apps/blob/main/workspaces/deafrica-prod-af/processing/argo/workflow-templates/stats-crop-mask.yaml) in the [datakube-apps](https://github.com/digitalearthafrica/datakube-apps) repo.

4. Change the parameters in the workflow template to align with the job you're running. A screen shot is shown below.

    * The `image-tag` number is the version number of the docker image i.e. the number [here](https://github.com/digitalearthafrica/crop-mask/blob/main/docker/version.txt)
    * The `result-bucket` is the location where the output geotiffs will be stored. This is `deafrica-services` if running the full production run, `deafrica-data-staging-af` if testing in production workspace, and `deafrica-data-dev-af` if running in the dev environment.
    * The `product-name` is the name of the crop mask being run e.g. "crop_mask_western", or "crop_mask_sahel" etc. 
    * The `product-cfg` is the _raw_ github https link to the plugin configuration yaml, e.g. one of the files [here](https://github.com/digitalearthafrica/crop-mask/tree/main/production/cm_tools/cm_tools/config)
    * `product-version` is usually just `1-0-0`, unless re-running a crop-mask with as a newer version.
    * `temporal-range` is the time range that gets passed to `odc-stats save tasks`; for the crop-mask this will _always_ take the format `<YYYY>--P1Y`, e.g. `2019--P1Y` to run a cropmask for 2019
    * `cropmask-region` is the region of Africa that is being run, ie. one of the eight regions corresponding to the crop-mask product being run e.g. `western`, or `sahel` etc. This parameter is used to clip the tiles being processed to a single region of Africa
    * `parallel-processing` refers to the number of pods K8s will scale too. For testing, set this to `1` and a single machine will run - this makes it easy to inspect logs etc.  For the full scale production runs a good number is `300` (300 machines will run 300 tiles in parallel).
    * The other parameters (`input-products`, `queue`, `resolution` etc.) should mostly stay as their defaults.
    * Hit the `submit` button when you're happy with the inputs and the code will be deployed.
    
    
<img align="centre" src="../figs/argo_workflow.PNG" width="65%">

5. To monitor the batch run you can use:
   
     * Production CPU, memory, SQS monitoring: https://mgmt.digitalearth.africa/d/CropMaskMetrics/crop-mask-annual
     * Dev CPU, memory, SQS monitoring: https://mgmt.dev.digitalearth.africa/d/CropMaskMetrics/crop-mask-annual

6. To check the logs of any pod, you can click on one of the pods that displays in Argo after you hit submit and then click the `logs` button 

7. Once the batch job has completed, you can follow the instructions in `2_Indexing_results_into_datacube.ipynb` to index the crop-mask into the datacube.


### Other useful run notes

* To list tiles in a s3 bucket; useful to know if results have been successfully written to disk
        
        aws s3 ls s3://deafrica-data-dev-af/crop_mask_western/
        
* To sync (copy) results in a s3 bucket to your local machine
        
        aws s3 sync s3://deafrica-data-dev-af/crop_mask_western/ crop_mask_western

* If doing test runs, and you wish delete test geotifs from the dev bucket
        
        aws s3 rm --recursive s3://deafrica-data-dev-af/crop_mask_western --dryrun

        
---
## Additional information

**License:** The code in this notebook is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).
Digital Earth Africa data is licensed under the [Creative Commons by Attribution 4.0](https://creativecommons.org/licenses/by/4.0/) license.

**Contact:** If you need assistance, please post a question on the [Open Data Cube Slack channel](http://slack.opendatacube.org/) or on the [GIS Stack Exchange](https://gis.stackexchange.com/questions/ask?tags=open-data-cube) using the `open-data-cube` tag (you can view previously asked questions [here](https://gis.stackexchange.com/questions/tagged/open-data-cube)).
If you would like to report an issue with this notebook, you can file one on [Github](https://github.com/digitalearthafrica/crop-mask/issues).



<!-- 3. Ensure the `datakube-apps` and `datakube` repositories have correctly configured pod/argo templates. Make sure the image version and config urls are correct.  For production, the files to consider are:

<!--     * Batch run job template: [06_stats_crop_mask.yaml](https://bitbucket.org/geoscienceaustralia/datakube-apps/src/master/workspaces/deafrica-prod-af/processing/statistician/06_stats_crop_mask.yaml)

    * Node group configuration (usually you shouldn't need to alter this): [workers.tf](https://bitbucket.org/geoscienceaustralia/datakube/src/37fbf47358d287aecefbe4f079bf5048f0295b82/workspaces/deafrica-prod-af/01_odc_eks/workers.tf#lines-126)  
    
    * Pod template (use this for testing): [06_stats_crop_mask_dev_pod.yaml](https://bitbucket.org/geoscienceaustralia/datakube-apps/src/master/workspaces/deafrica-prod-af/processing/statistician/06_stats_crop_mask_dev_pod.yaml)

4. Use your dev-box to access the `deafrica-prod-af-eks` environment

        setup_aws_vault deafrica-prod-af-eks
        ap deafrica-prod-af-eks

5. Create a dev-pod by running:
            
        kubectl apply -f workspaces/deafrica-prod-af/processing/statistician/06_stats_crop_mask_dev_pod.yaml
    

6. Access the dev-pod by runnning:

        kubectl exec -it crop-mask-dev-pod -n processing -- bash
        

7. Once in the dev-pod we need to create a large set of database 'tasks' that odc-stats will use as inputs to our ML pipeline (tile information). Run:

        odc-stats save-tasks --frequency annual --grid africa-10 gm_s2_semiannual
        

8. The database files created by running the above command now needs to be synced to the product's S3 bucket. Run:
    
        aws s3 sync . s3://deafrica-services/<product>/<version>/db-files --acl bucket-owner-full-control


9. To execute a batch run, we need to publish a list of tiles to AWS's Simple Queue Service. The command `cm-tsk` will use a geojson (e.g. `Western.geojson`) to clip the tasks to just a single region of Africa (defined by the extent of the geojson), and send those tasks/messages to SQS.

        cm-task --task-csv=gm_s2_semiannual_all.csv --geojson=/western/Western.geojson --outfile=/tmp/aez.csv --sqs deafrica-prod-af-eks-stats-crop-mask --db=s3://deafrica-services/crop_mask_eastern/1-0-0/gm_s2_semiannual_all.db


9. Exit the dev-pod using `exit`, and then trigger the batch run using the command: **Note, confirm that the k8s service user for the crop-mask has permissions write to deafrica-services bucket (sometimes this can automatically reset so needs to be checked before each run)** 

        kubectl -n processing apply -f workspaces/deafrica-prod-af/processing/statistician/06_stats_crop_mask.yaml


10. To monitor the batch run you can use:
   
     - CPU and memory monitoring: https://mgmt.digitalearth.africa/d/wIVvTqR7k/crop-mask
     - SQS and instance monitoring: https://monitor.cloud.ga.gov.au/d/n2TdQCnnz/crop-mask-dev-deafrica?orgId=1

11. To move deadletter items back into the SQS queue, go into the dev pod, start python and run the following:
        
        >>> from odc.aws.queue import redrive_queue
        >>> redrive_queue('deafrica-prod-af-eks-stats-crop-mask-deadletter', 'deafrica-prod-af-eks-stats-crop-mask') -->

<!-- ---
## Other useful run notes

* Restarting the job if timeout errors prevent all messages being consumed:

     - Check the logs of multiple jobs
     - If multiple logs show the time-out error, then delete the job with `kubectl -n processing delete jobs crop-mask-ml-job`
     - Restart the job: `kubectl apply -f workspaces/deafrica-prod-af/processing/06_stats_crop_mask.yaml -n processing`

* To delete all messages from SQS queue:

     - go to AWS central app, open SQS, click on the queue you want to remove and hit the delete button

* To list tiles in a s3 bucket; useful to know if results have been successfully written to disk
        
        aws s3 ls s3://deafrica-data-dev-af/crop_mask_western/
        
* To sync (copy) results in a s3 bucket to your local machine
        
        aws s3 sync s3://deafrica-data-dev-af/crop_mask_western/ crop_mask_western

* If doing test runs, and you wish delete test geotifs from the dev bucket
        
        aws s3 rm --recursive s3://deafrica-data-dev-af/crop_mask_western --dryrun

* To test running one or two tiles in the dev-pod, you can directly run the `cm-pred` command

```
odc-stats run s3://deafrica-services/crop_mask_eastern/1-0-0/gm_s2_semiannual_all.db --config=${CFG} --resolution=10 --threads=15 --memory-limit=100Gi --location=s3://deafrica-data-dev-af/{product}/{version} 719:721
```

* Useful kubectl commands you'll need
       
        # See what pods are running
        kubectl get pods -n processing
        
        # See what jobs are running
        kubectl get jobs -n processing
        
        # Check the logs of a job
        kubectl logs <job-id> -n processing 
        
        # Delete a batch job
        kubectl delete jobs <job name> - processing 
        
        # Shut down pod
        kubectl delete pods <pod name> -n processing 
        
        kubectl get deployment -n processing
        
        kubectl -n processing describe pod crop-mask-dev-pod -->
 -->
