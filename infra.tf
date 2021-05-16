variable "region" {
  default = "us-east-1"
}

variable "availability_zone_suffix" {
  default = "a"
}

variable "s3_bucket" {
  default = "cdg-osr2mp4"
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.40"
    }
  }

  backend "s3" {
    bucket = "cdg-osr2mp4"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      terraform = true
      project   = local.project_name
    }
  }
}

locals {
  availability_zone = "${var.region}${var.availability_zone_suffix}"
  cidr_block        = "10.0.0.0/28"
  fs_root           = "/mnt/efs"
  project_name      = "osr2mp4"
}

resource "aws_s3_bucket" "bucket" {
  bucket = var.s3_bucket

  lifecycle_rule {
    enabled = true
    prefix  = "mp4/"

    expiration {
      days = 1
    }
  }
}

resource "aws_ecr_repository" "repo" {
  name = local.project_name
}

data "aws_ecr_image" "img" {
  repository_name = aws_ecr_repository.repo.name
  image_tag       = "latest"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "inline_policy" {
  statement {
    resources = ["*"]
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
  }
}

resource "aws_iam_role" "role" {
  name               = local.project_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  inline_policy {
    name   = local.project_name
    policy = data.aws_iam_policy_document.inline_policy.json
  }
}

resource "aws_lambda_function" "fn" {
  function_name = "${local.project_name}-record"
  role          = aws_iam_role.role.arn
  image_uri     = "${aws_ecr_repository.repo.repository_url}@${data.aws_ecr_image.img.image_digest}"
  # memory_size   = 10240
  # timeout       = 900
  package_type = "Image"

  environment {
    variables = {
      FS_ROOT = local.fs_root
    }
  }

  file_system_config {
    arn              = aws_efs_access_point.ap.arn
    local_mount_path = local.fs_root
  }

  image_config {
    command           = ["app.handler"]
    entry_point       = ["python", "-m", "awslambdaric"]
    working_directory = "/"
  }

  vpc_config {
    security_group_ids = [aws_security_group.lambda.id]
    subnet_ids         = [aws_subnet.subnet.id]
  }
}

resource "aws_vpc" "vpc" {
  cidr_block = local.cidr_block
}

resource "aws_subnet" "subnet" {
  vpc_id            = aws_vpc.vpc.id
  availability_zone = local.availability_zone
  cidr_block        = local.cidr_block
}

resource "aws_security_group" "lambda" {
  name   = "${local.project_name}-lambda"
  vpc_id = aws_vpc.vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "efs" {
  name   = "${local.project_name}-efs"
  vpc_id = aws_vpc.vpc.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
}

resource "aws_efs_file_system" "fs" {
  availability_zone_name = local.availability_zone
  creation_token         = local.project_name
}

resource "aws_efs_access_point" "ap" {
  file_system_id = aws_efs_file_system.fs.id

  posix_user {
    gid = 0
    uid = 0
  }
}

resource "aws_efs_mount_target" "mount" {
  file_system_id  = aws_efs_file_system.fs.id
  subnet_id       = aws_subnet.subnet.id
  security_groups = [aws_security_group.efs.id]
}

output "repo_url" {
  value = aws_ecr_repository.repo.repository_url
}
