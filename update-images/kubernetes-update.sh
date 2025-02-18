#!/bin/bash

parent_path=$( cd "$(dirname "$0")" ; pwd -P )
cd "$parent_path"

# Set context to desired environment
ENV="acceptance"
kubectl config set-context arn:aws:eks:eu-west-2:824841205322:cluster/dissco-k8s-acceptance

for dir in ../"$ENV"/*/; do
  for filepath in "$dir"*yaml; do
    kubectl apply -f "$filepath"
  done
done