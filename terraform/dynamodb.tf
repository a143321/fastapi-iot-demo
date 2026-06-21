# terraform/dynamodb.tf
resource "aws_dynamodb_table" "iot_data" {
  name           = "IoTData"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "device_id"
  range_key      = "timestamp"

  attribute {
    name = "device_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }
}
