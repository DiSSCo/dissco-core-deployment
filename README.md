# dissco-core-deployment
DiSSCo core deployment contains all files necessary for deploying the DiSSCo core applications.
This consists of two parts:
- Deployment of helm charts
- Deployment of DiSSCo resources

The repo is divided into the different environments (development/acceptance/production).

## Deployment of helm charts 
The deployment of the helm charts in the helm folder (for example `acceptance-argocd`) is done by the [infrastructure pipeline](https://github.com/DiSSCo/dissco-core-infrastructure).
These helm charts contain operators and application which are needed to run the DiSSCo core infrastructure.
The principle of [App-of-Apps](https://argo-cd.readthedocs.io/en/stable/operator-manual/cluster-bootstrapping/) is used.
We bundled the deployment of the ArgoCD deployments into a single helm chart.
This helm chart is deployed on the cluster and manages all the underlying helm charts.
Any changes can be made in this repo and pushed.
When it is merged in the `main` branch, argoCD will trigger and update the cluster.
The helm charts contain:
- Elastic stack operator, adds CRDs for the deployment of elastic resources
- KEDA, adds CRDs and applications for the management of KEDA resources
- Metrics servers, deploys Kubernetes native metrics service, required for things such as `kubectl top node`
- Secret Driver AWS, deploys application for the secret driver for AWS
- Secret Manager, deploys application for the management of secrets (needs AWS driver for AWS Secret Store)
- Strimzi, adds CRDs and operator for the management of Kafka

## Deployment of DiSSCo resources
The deployment of the DiSSCo resources happens by deploying the `argocd-deployment.yaml`.
This deployment needs to be done manually.
This will trigger ArgoCD to deploy all resource (recursive) in a particular folder.
This deployment will include:
- Traefik, this deploys the CRD and Ingress, including all security settings. No good Helm chart exists for how we use it, so deployment of resources is necessary
- Elasticsearch + Kibana, deploys a HA cluster (3) of Elasticsearch and a Kibana instance
- Kafka, deploys a HA kafka cluster (3) together with the required ZooKeepers (3)
- Secret Manager, resources needed to inject the AWS Secret Store secrets into Kubernetes
- DiSSCo applications

### DiSSCo applications
The DiSSCo applications are structured so that they are self-containing packages.
Each folder includes everything needed to run the service, this may contain:
- Deployment file
- Service, for internal connectivity
- KEDA files, for automated scaling
- IngressRoute, for routing
- Kafka topic, for messages

## Change management
After all applications are deployed, all changes should be made by creating PR's on the repo and merge them to `main`.
ArgoCD monitors the `main` branch of the GitHub repo.
When new changes are made it will automatically recognise that kubernetes is no longer in sync with the files in the repo.
It can then automatically synchronise the cluster with the changed kubernetes files.
There is also an option to leave the actual syncrhonisation a manual action.

## Kube Green
The installation of kube-green is still  manual.
Follow the steps on this website: https://kube-green.dev/docs/install/
