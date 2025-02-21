# Crea el archivo ZIP con el cÃ³digo de la lambda (si no existe)
resource "null_resource" "create_zip" {
  triggers = {
    # Cada vez que cambie algo en el archivo lambda_function.py, se dispara el recurso
    source_hash = filebase64sha256("lambda_function.py")
  }

  provisioner "local-exec" {
    command = "zip -j lambda_function.zip lambda_function.py"
    working_dir = path.module  # Asegura que el zip se crea en el directorio correcto
  }
}

resource "aws_lambda_function" "dns_updater" {
  function_name    = "dns_updater_lambda"
  role            = aws_iam_role.lambda_role.arn
  handler        = "lambda_function.lambda_handler"
  runtime        = "python3.8"
  filename       = "../python/lambda_function.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_dns_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "lambda_dns_policy"
  description = "IAM policy for Lambda DNS updater"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["ec2:DescribeTags", "ec2:DescribeInstances", "route53:ChangeResourceRecordSets"]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}