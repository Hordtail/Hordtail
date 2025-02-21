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
  function_name    = "brais_lambda"
  role            = aws_iam_role.lambda_role.arn
  handler        = "lambda_function.lambda_handler"
  runtime        = "python3.9"
  filename       = "lambda_function.zip"

  environment {
    variables = {
      DOMAIN_NAME_B = "brais"  # Reemplaza con tu dominio real
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_dns_role_brais"

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
  name        = "lambda_dns_policy_brais"
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

# Define la regla para capturar eventos de EC2
resource "aws_cloudwatch_event_rule" "ec2_launch_rule" {
  name        = "ec2-launch-rule"
  description = "Regla para invocar Lambda cuando se lance una instancia EC2"
  event_pattern = jsonencode({
    "source"        = ["aws.ec2"],
    "detail-type"   = ["EC2 Instance State-change Notification"],
    "detail" = {
      "state" = ["running"]
    }
  })
}

# Permisos para que CloudWatch Events invoque Lambda
resource "aws_lambda_permission" "allow_cloudwatch_invoke" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dns_updater.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_launch_rule.arn
}

# Define el target para invocar la Lambda
resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule      = aws_cloudwatch_event_rule.ec2_launch_rule.name
  arn       = aws_lambda_function.dns_updater.arn
}

resource "aws_iam_role_policy" "lambda_route53_permissions" {
  name = "lambda-route53-policy"
  role = aws_iam_role.lambda_role.id  # Asegúrate de que este sea el ID de tu rol Lambda

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "route53:ChangeResourceRecordSets",
          "route53:ListResourceRecordSets"
        ],
        "Resource" : [
          "arn:aws:route53:::hostedzone/YOUR_HOSTED_ZONE_ID"
        ]
      }
    ]
  })
}
resource "aws_iam_policy" "lambda_logs_policy" {
  name        = "LambdaLogsPolicy"
  description = "Permisos para que Lambda cree y escriba en CloudWatch Logs"
  
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "*"
      }
    ]
  })
}


resource "aws_instance" "brais_instance_lambda" {
  ami           = "ami-02e2af61198e99faf"  # Asegúrate de usar una AMI válida
  instance_type = "t3.micro"
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.vpc_security_group_ids]

  tags = {
    Name        = "Instance_Lambda_brais"
    DomainName  = var.domain_name  # Usando la variable `domain_name` de Terraform
  }
}
