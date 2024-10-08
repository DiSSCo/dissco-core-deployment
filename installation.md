# How to setup a new environment from scratch

## Make sure infrastructure is deployed
First deploy all infrastructure necessary for the applications using TerraFrom,see the [infrastructure repo](https://github.com/DiSSCo/dissco-core-infrastructure). 
If this was deployed successfully you should now have a document-db, rds postgres database and a kubernetes cluster. 
On the kubernetes cluster you should have ArgoCD deployed with all the shared-resources. 
These shared resources consists of some overhead needed to deploy CRDs.

## Synchronize helm charts
The second step is to synchronise the helm charts. 
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

For the elasticsearch, mongodb and handle api secrets we need to create a new secret.
To get the elasticsearch credentials we first need to start the elasticsearch deployment by running:
`k apply -f elastic/`
This will create, among other things, a secret called `elastic-search-es-elastic-user` which can be retrieved with:
`k get secret -n elastic elastic-search-es-elastic-user -o yaml` which we can decrypt with `echo {password} |base64 -d`
We will add the result to the secret.
The mongodb string can be added by getting the connectionstring from the AWS resources and replacing the password with the password used in the infrastructure files.
Now create the secret and copy the ARN to the aws-secret ARN.
Last we can add the handle api secret, we can retrieve it from Keycloak.

The secrets can now be added with:
`k apply -f secret-manager/`

## Create database and create tables
Database should be able to receive public connections with IP whitelisted in the dissco-infrastructure repo.
Setup a connection and manually create the dissco database.
`create database dissco with owner disscomasteruser;`
Then you will be able to create all dissco tables by applying the sql files in the database folder of this repo.

## Setup indices for elastic
This can be done through different ways, here we will use Kibana dev tools.
Create a port-forward to kibana:
`k port-forward -n elastic service/kibana-kb-http 5601`
Go to `https://localhost:5601/app/home#/` and login with the elastic user creds.
Then go to dev tools and add the mappings available in this repository.

## Setup indices for mongodb

Note: the following is also possible through a user interface using a tool such as [MongoDB Compass](https://www.mongodb.com/products/tools/compass). 

We need to add some additional indices on mongodb to make sure we can quickly grap the version numbers of the objects.
We will put the version on each PID (instead of the default which is on PID/version)
This step is a bit tricky as mongodb is not publicly exposed so we need an app in the network to reach mongodb
`kubectl run my-shell --rm -i --tty --image ubuntu -- bash`
Then run the installation steps for mongosh
https://www.mongodb.com/docs/mongodb-shell/install
`mongosh <connection-string>` Use connection string from secret but remove additional query params
`use dissco`
Run the following create index comments
```
db.digital_specimen_provenance.createIndex(
  {
      "prov:Entity.prov:value.@id": 1
  }
)

db.digital_specimen_provenance.createIndex(
  {
      "prov:Entity.prov:value.ods:version": 1
  }
)

db.annotation_provenance.createIndex(
  {
      "prov:Entity.prov:value.@id": 1
  }
)

db.annotation_provenance.createIndex(
  {
      "prov:Entity.prov:value.ods:version": 1
  }
)


db.digital_media_provenance.createIndex(
  {
      "prov:Entity.prov:value.@id": 1
  }
)

db.digital_media_provenance.createIndex(
  {
      "prov:Entity.prov:value.ods:version": 1
  }
)
```

Now we can exit and delete the pod
`.exit`
`exit`
`k delete pod my-shell`

It may take several minutes to create the indexes.

## Add Kafka and traefik
We can now add Kafka by applying the yaml to the cluster.
Next we can also add the ingress, this creates the external IP we need for the DNS record.

## Add backend then create all other resources
Now it is easiest to first deploy the dissco-backend as it will generate the secrets based on the AWS secret manager.
It also tests most of the connectivity as it requires several connections.
If this is all successfully continue with deploying the other applications.

Make sure all applications are running.

## Commit the files to github
Commit all changes to github from now on this is the place where all changes will be made.

## Enable resizing of PVC 
Add scaling property to EKS disk.
Edit storageclass `gp2` and add `allowVolumeExpansion: true`
`kubectl edit sc gp2`
https://www.jeffgeerling.com/blog/2019/expanding-k8s-pvs-eks-on-aws

## Deploy the argocd deployment to synchronize with the github repo

