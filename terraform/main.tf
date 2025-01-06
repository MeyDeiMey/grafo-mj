# terraform/main.tf

provider "aws" {
  region     = "us-east-1"
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
  token      = var.aws_session_token
}

variable "aws_access_key_id" {}
variable "aws_secret_access_key" {}
variable "aws_session_token" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# 1. Security Group
resource "aws_security_group" "graph_sg" {
  name        = "graph_sg"
  description = "Allow inbound on port 5000"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. EC2 instance
resource "aws_instance" "graph_ec2" {
  ami           = "ami-0e731c8a588258d0d"  # Amazon Linux 2023 (ejemplo, ajústalo)
  instance_type = "t2.micro"
  subnet_id     = tolist(data.aws_subnets.default.ids)[0]
  vpc_security_group_ids = [aws_security_group.graph_sg.id]

  associate_public_ip_address = true  # Asegura que la instancia tenga una IP pública


  # user_data: clonar tu repo, instalar dependencias, iniciar la API
  user_data = <<-EOF
    #!/bin/bash
    dnf update -y
    dnf install -y python3-pip git

    # Clonar tu repo con la carpeta datamart ya poblada (o genera la datamart en local y haz commit)
    cd /home/ec2-user
    git clone https://github.com/JoaquinIP/graphword-mj
    cd graphword-mj

    pip3 install -r requirements.txt
    pip3 install gunicorn

    # Navegar al directorio de la aplicación Flask
    cd /home/ec2-user/graphword-mj/app
    
    # Levantar la API con Gunicorn
    nohup gunicorn --bind 0.0.0.0:5000 api:app > app.log 2>&1 &
  EOF

  tags = {
    Name = "GraphWordInstance"
  }
}

# 3. (Opcional) API Gateway
resource "aws_apigatewayv2_api" "graph_api" {
  name          = "graph-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "http_proxy" {
  api_id            = aws_apigatewayv2_api.graph_api.id
  integration_type  = "HTTP_PROXY"
  integration_uri   = "http://${aws_instance.graph_ec2.public_dns}:5000/"
  connection_type   = "INTERNET"
  integration_method = "ANY"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.graph_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.http_proxy.id}"
}

resource "aws_apigatewayv2_stage" "dev" {
  api_id      = aws_apigatewayv2_api.graph_api.id
  name        = "dev"
  auto_deploy = true
}

output "api_endpoint" {
  value = aws_apigatewayv2_stage.dev.invoke_url
}

output "ec2_public_dns" {
  value = aws_instance.graph_ec2.public_dns
}
