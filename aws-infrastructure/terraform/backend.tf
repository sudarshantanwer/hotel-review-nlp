terraform {
  backend "s3" {
    bucket         = "hotel-review-nlp-terraform-state-1764534382"
    key            = "prod/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "hotel-review-nlp-terraform-lock"
    encrypt        = true
  }
}
