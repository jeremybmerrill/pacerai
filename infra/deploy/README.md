# Deployment Readme

This project's server setup is managed by Terraform and the app code is managed by AWS Code Deploy.

Terraform is a tool where we declaratively define the AWS resources we want, then Terraform ensures they exist. It's important not to make modifications in the AWS console, because that will confuse Terraform (and Terraform will undo manual changes upon the next deployment.)

## Help! I need to make a change to the server config quickly!

You can go ahead and make it manually in the AWS console if it's an emergency-emergency. Be sure to reflect that change in hearkenmodels.tf afterwards, or, alternatively, make the change first, then apply the changes.

## How do I make changes to the server config?

Make a chance in hearkenmodels.tf, then type `terraform apply` in the `deploy/` directory. You'll have to type "yes" to confirm it, but do be sure to read Terraform's explanation of what it plans to do, to make sure it makes sense.

## How do I deploy app changes?

`bash deploy.sh`. It deploys your current working directory; source control (and/or CI) are up to you.

## manual setup steps, taken once:

Create resources to keep Terraform state.

- `gni-hearken-ai-models-deployment` S3 bucket manages Terraform state AND holds the CodeDeploy objects. Created manually, with Bucket Versioning turned on.
- `gni-hearken-ai-models-terraform-state-locking` DynamoDB table with `string` type Primary Key called `LockID`. Tag `Project` = `gni-hearken-ai-models` Be sure it's in us-east-1!

as usual:

`terraform apply`
`bash deploy/deploy.sh` 

- upload .env to the web server with correct values set, including the database credentials (which are output from `terraform apply`)