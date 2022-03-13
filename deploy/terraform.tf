

# deploy with `infra/deploy$` `pushd ../../rss_scraper/ && zip -D -r ../infra/deploy/rss_scraper_lambda.zip . --exclude="*.env" && popd && AWS_PROFILE=personal terraform apply` 

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }
  backend "s3" {
    bucket = "tow-pacer-terraform-state"
    key    = "tf"
    region = "us-east-1"
    dynamodb_table = "tow-pacer-terraform-state-locking"
    profile = "personal"
  }  
}

provider "aws" {
  profile = "personal"
  region  = "us-east-1"
}

variable "name" {
  default = "tow-pacer"
}

variable "username" { # for database
  default =  "towpacer"
}

variable "scraper_lambda_function_name" {
  default = "tow-pacer-data-scraper"
}

variable "jeremys_ip_cidr_block" { # e.g. 1.2.3.4/32 for your home IP.
  nullable = false
}

resource "aws_key_pair" "towpacer" {
  key_name   = "towpacer"
  public_key = file(pathexpand("~/.ssh/towpacer.pub"))
}

resource "random_id" "database_password" {
  keepers = {
    password = var.username
  }

  byte_length = 16
}

resource "random_id" "random" {
  keepers = {
    password = var.name
  }

  byte_length = 8
}


resource "aws_s3_bucket" "pacerporcupine" {
  bucket = "pacerporcupine"
  acl    = "public-read"

  website {
    index_document = "index.html"
    error_document = "error.html"
  }
  tags = {
    Project     = "tow-pacer"
  }    
}

resource "aws_s3_bucket" "pacerporcupine-deployment" {
  bucket = "tow-pacer-deployment2"
  tags = {
    Project     = "tow-pacer"
  }    
}



resource "aws_security_group" "db_security_group" {
  name        = "${var.name} rds security group"
  description = "Managed by Terraform"

  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    # security_groups = [aws_security_group.security_group.id]
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_cloudwatch_log_group" "data-scraper" {
  name              = "/aws/lambda/${var.scraper_lambda_function_name}"
  retention_in_days = 14
}

# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
resource "aws_iam_policy" "lambda_logging" {
  name        = "lambda_logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}



# resource "aws_lambda_function" "pacer_rss_scraper" {
#   function_name    = var.scraper_lambda_function_name
#   handler          = "rss_data_gatherer.scrape_all_courts"
#   runtime          = "python3.7"
#   memory_size      = 512
#   timeout          = 900
#   role             = aws_iam_role.iam_for_lambda.arn
#   source_code_hash = filebase64sha256("rss_scraper_lambda.zip")
#   filename      = "rss_scraper_lambda.zip"

#   environment {
#     variables = {
#       DATABASE_URL     = "postgresql://${aws_db_instance.ai_db_instance.username}:${aws_db_instance.ai_db_instance.password}@${aws_db_instance.ai_db_instance.address}/${aws_db_instance.ai_db_instance.name}" 
#     }
#   }
#   tags = {
#     Name        = "${var.name}-api-database"
#     Project     = "tow-pacer"
#   }  
# }



# resource "aws_cloudwatch_event_rule" "every_two_hours_during_business_hours" {
#     name = "every-two-hours-during-biz-hours"
#     description = "Fires every two hours during business hours, Mon-Fri"
#     schedule_expression = "cron(0 8-22/2 ? * MON-FRI *)"
# }

# resource "aws_cloudwatch_event_target" "scrape_pacer_rss_every_five_minutes" {
#     rule = aws_cloudwatch_event_rule.every_two_hours_during_business_hours.name
#     target_id = "pacer_rss_scraper"
#     arn = aws_lambda_function.pacer_rss_scraper.arn
# }

# resource "aws_lambda_permission" "allow_cloudwatch_to_call_check_foo" {
#     statement_id = "AllowExecutionFromCloudWatch"
#     action = "lambda:InvokeFunction"
#     function_name = aws_lambda_function.pacer_rss_scraper.function_name
#     principal = "events.amazonaws.com"
#     source_arn = aws_cloudwatch_event_rule.every_two_hours_during_business_hours.arn
# }



resource "aws_db_instance" "ai_db_instance" {
  identifier             = "${var.name}-db"
  allocated_storage      = "16"
  storage_type           = "gp2"
  engine                 = "postgres"
  engine_version         = "12.7"
  instance_class         = "db.t3.micro"
  vpc_security_group_ids = [aws_security_group.db_security_group.id]
  deletion_protection    = true
  final_snapshot_identifier = "${var.name}-final-snapshot-${random_id.database_password.hex}"
  backup_retention_period = 14
  copy_tags_to_snapshot = true

  tags = {
    Name        = "${var.name}-api-database"
    Project     = "tow-pacer"
  }

  name     = "${replace(var.name, "-", "")}db"
  username = var.username
  password = random_id.database_password.hex
}

output "database_address" {
  value = aws_db_instance.ai_db_instance.address
}

output "database_dbname" {
  value = aws_db_instance.ai_db_instance.name
}

output "database_username" {
  value = aws_db_instance.ai_db_instance.username
}

output "database_password" {
  value = aws_db_instance.ai_db_instance.password
  sensitive = true
}

##############################################
# Server
##############################################


resource "aws_iam_role" "s3_readerwriter_access_role" {
  name               = "s3-role"
  assume_role_policy = jsonencode({
   "Version": "2012-10-17",
   "Statement": [
     {
       "Action": "sts:AssumeRole",
       "Principal": {
         "Service": "ec2.amazonaws.com"
       },
       "Effect": "Allow",
       "Sid": ""
     }
   ]
  })
}
data "aws_iam_policy_document" "s3_readerwriter_policy_document" {
  statement {
    sid = "1"

    actions = [
      "s3:*",
      "s3:*",
    ]

    resources = [
      "arn:aws:s3:::${aws_s3_bucket.pacerporcupine.bucket}/*",
      "arn:aws:s3:::${aws_s3_bucket.pacerporcupine-deployment.bucket}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_readerwriter_policy" {
  name        = "${var.name}_s3_readerwriter_policy"
  description = "Lets the pacerporcupine ML service talk to S3 to read/write (mostly model artifacts)"
  policy = data.aws_iam_policy_document.s3_readerwriter_policy_document.json
}

resource "aws_iam_policy_attachment" "s3_readerwriter-attach" {
  name       = "${var.name}_s3_readerwriter-attachment"
  roles      = [
    aws_iam_role.s3_readerwriter_access_role.name, 
    aws_iam_role.codedeploy_role.name
    ]
  policy_arn = aws_iam_policy.s3_readerwriter_policy.arn
}


resource "aws_iam_instance_profile" "s3_readerwriter" {
  name  = "${var.name}_s3_readerwriter"
  role = aws_iam_role.s3_readerwriter_access_role.name
}


resource "aws_security_group" "security_group" {
  name        = "${var.name} security group"
  description = "Managed by Terraform"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.jeremys_ip_cidr_block]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.jeremys_ip_cidr_block]
  }


  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.jeremys_ip_cidr_block]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.jeremys_ip_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


data "aws_ami" "amazon-linux-2" {
 most_recent = true
 owners           = ["amazon", "099720109477"]

 # filter {
 #   name   = "name"
 #   values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20210511"]
 # }
 filter {
   name = "image-id"
   values = ["ami-02069978db500a511"]
 }
}

resource "aws_instance" "ai_server" {
  ami             = data.aws_ami.amazon-linux-2.id
  instance_type        = "t3.medium"
  root_block_device {
    volume_size          = 80
  }
  vpc_security_group_ids      = [aws_security_group.security_group.id]
  iam_instance_profile = aws_iam_instance_profile.s3_readerwriter.name
  key_name             = aws_key_pair.towpacer.key_name
  tags = {
    Name        = "${var.name}-ai-server"
    Contact     = "Jeremy Merrill"
    Project     = "tow-pacer"
  }
  user_data       = data.template_file.userdata_ai_server.rendered
  lifecycle {
    # prevent_destroy = true
    ignore_changes = [user_data]
  }

}
data "template_file" "userdata_ai_server" {
  template = file("image_install_script.sh")
}



resource "aws_iam_role" "codedeploy_role" {
  name = "${var.name}-codedeploy_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "codedeploy.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "AWSCodeDeployRole" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"
  role       = aws_iam_role.codedeploy_role.name
}


resource "aws_codedeploy_app" "application" {
  name = var.name
}


resource "aws_codedeploy_deployment_group" "application" {
  app_name              = aws_codedeploy_app.application.name
  deployment_group_name = "production"
  service_role_arn      = aws_iam_role.codedeploy_role.arn

  ec2_tag_set {
    ec2_tag_filter {
      key   = "Name"
      type  = "KEY_AND_VALUE"
      value = "${var.name}-ai-server"
    }
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE"]
  }

}

output "ai_server_url" {
  value = aws_instance.ai_server.public_dns
}
