variable "domain_name" {
  type        = string
  description = "The domain name to tag the EC2 instance"
  default     = "brais"  # Aquí puedes poner el valor que desees
}
variable "subnet_id" {
  default = "subnet-0d7c82de853291508"
}
 variable "vpc_security_group_ids" {
  default = "sg-07e49b2ac92e54af9"
 }