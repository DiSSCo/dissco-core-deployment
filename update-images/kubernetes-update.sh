#!/bin/bash

set -euo pipefail

parent_path=$( cd "$(dirname "$0")" ; pwd -P )
cd "$parent_path"

# Set context to desired environment (acc) or production
ENV="acc"
kubectl config use-context arn:aws:eks:eu-west-2:824841205322:cluster/dissco-k8s-"$ENV"

kubectl config get-contexts

echo "Continue with update? (y)"

read RESPONSE

if  [[ "$RESPONSE" = "y" ]]; then
  # Read the output of update-images.py, apply the changed files
  while read p; do
    kubectl apply -f ../"$p"
  done <../file_names.txt
  else
    echo "Images not updated. Exiting program"
fi

