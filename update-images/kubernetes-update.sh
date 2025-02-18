#!/bin/bash

parent_path=$( cd "$(dirname "$0")" ; pwd -P )
cd "$parent_path"

# Set context to desired environment (acc) or production
ENV="acc"
kubectl config set-context arn:aws:eks:eu-west-2:824841205322:cluster/dissco-k8s-"$ENV"

# Read the output of update-images.py, apply the changed files
while read p; do
  kubectl apply -f ../"$p"
done <../file_names.txt