create an application and a deployment group in AWS CodeDeploy.

For the deployment group, specify the name (production), service role (as created in Terraform, but `arn:aws:iam::612251176106:role/qzaifbdb-deployment`) Environment configuration (EC2, select the name of the instance named in Terraform and no load-balancing (for now!).)

Oddly, sometimes teh userdata from Terraform doesn't run and you have to do it yourself.