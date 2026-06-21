variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "fastapi-iot-demo"
}

variable "container_port" {
  description = "Port the container is listening on"
  type        = number
  default     = 8000
}
