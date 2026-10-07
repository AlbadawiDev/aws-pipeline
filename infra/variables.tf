variable "aws_region" {
  description = "AWS region for a future explicitly approved deployment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Resource name prefix. The S3 bucket receives a unique suffix."
  type        = string
  default     = "portfolio-pipeline"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project_name))
    error_message = "Use 3 to 31 lowercase letters, digits or hyphens, starting with a letter."
  }
}
