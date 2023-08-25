# How to setup a new environment from scratch

## Make sure infrastructure is deployed
First deploy all infrastructure necessary for the applications using TerraFrom,see the [infrastructure repo](https://github.com/DiSSCo/dissco-core-infrastructure). 
If this was de deployed succesfully you should now have a document-db, rds postgres database and a kubernetes cluster. 
On the kubernetes cluster you should have ArgoCD deployed with all the shared-resources. 
These shared resources consists of some overhead needed to deploy CRDs.

## Synchronize helm charts
The second step is to synchonize the helm charts. 
You can now open the ArgoCD portal by using `k port-forward -n argocd service/argo-cd-argocd-server 8080:80`  
The password can be found by getting it from the cluster with:
`k get secret -n argocd argocd-initial-admin-secret -o yaml`
and decoding the password with `echo {password} | base64 -d`

We then synchronize all the helm charts in ArgoCD.
For the elastic chart, it might be required to deploy the `elastic` namespace with:
`k create ns elastic`

## Add secrets to AWS Secret 
There are two secrets we need to configure.
The database secrets were generated with the creation of the database. 
For this secret we need to get the ARN and place it in the db-secrets file.

For the elasticsearch and mongodb secrets we need to create a new secret.
To get the elasticsearch credentials we first need to start the elasticsearch deployment by running:
`k apply -f elastic/`
This will create, among other things, a secret called `elastic-search-es-elastic-user` which can be retrieved with:
`k get secret -n elastic elastic-search-es-elastic-user -o yaml` which we can decrypt with `echo {password} |base64 -d`
We will add the result to the secret.
The mongodb string can be added by getting the connectionstring from the AWS resources and replacing the password with the password used in the infrastructure files.
Now create the secret and copy the ARN to the aws-secret ARN.

The secrets can now be added with:
`k apply -f secret-manager/`

## Create database, tables and elastic schemas

