provider "aws" {
  region     = "us-east-1"
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
  token      = var.aws_session_token
}

# Variables permanecen igual...
variable "aws_access_key_id" {}
variable "aws_secret_access_key" {}
variable "aws_session_token" {}
variable "key_name" {
  description = "Nombre del Key Pair para SSH"
  type        = string
}
variable "public_key_path" {
  description = "Ruta a la llave pública SSH"
  type        = string
}

# Resources permanecen igual...
resource "aws_key_pair" "deployer" {
  key_name   = var.key_name
  public_key = file(var.public_key_path)
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security Group corregido para incluir puerto 5001
resource "aws_security_group" "graph_sg" {
  name        = "graph_sg"
  description = "Security group for graph application"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP"
  }

  ingress {
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow Flask application"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow SSH"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "graph_sg"
  }
}

# EC2 Instance con user_data corregido
resource "aws_instance" "graph_ec2" {
  ami                    = "ami-0e731c8a588258d0d"
  instance_type          = "t2.micro"
  subnet_id              = tolist(data.aws_subnets.default.ids)[0]
  vpc_security_group_ids = [aws_security_group.graph_sg.id]
  key_name               = aws_key_pair.deployer.key_name
  associate_public_ip_address = true

  user_data = <<-EOF
#!/bin/bash
set -e
exec > /var/log/user-data.log 2>&1

echo "Starting EC2 configuration"

# Update packages
dnf update -y
dnf install -y python3-pip git nginx python3-devel
echo "Package update completed"

# Clone repository
cd /home/ec2-user
git clone https://github.com/MeyDeiMey/grafo-mj.git
echo "Repository cloned"

# Configure Nginx
cat > /etc/nginx/conf.d/graphword.conf << 'EONG'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EONG

# Remove default nginx config
rm -f /etc/nginx/conf.d/default.conf

# Install Python dependencies
cd /home/ec2-user/ultimoBaile-TSCD/app
pip3 install -r requirements.txt
pip3 install gunicorn flask-cors networkx

# Start Nginx
systemctl enable nginx
systemctl restart nginx

# Start Flask application
cd /home/ec2-user/ultimoBaile-TSCD/app
nohup gunicorn --bind 127.0.0.1:5001 --log-level debug api:app > /home/ec2-user/gunicorn.log 2>&1 &

# Set permissions
chown -R ec2-user:ec2-user /home/ec2-user
EOF

  tags = {
    Name = "GraphWordInstance"
  }
}

# API Gateway con CORS habilitado
resource "aws_apigatewayv2_api" "graph_api" {
  name          = "graph-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
  }
}

resource "aws_apigatewayv2_integration" "http_proxy" {
  api_id             = aws_apigatewayv2_api.graph_api.id
  integration_type   = "HTTP_PROXY"
  integration_uri    = "http://${aws_instance.graph_ec2.public_dns}"
  integration_method = "ANY"
  connection_type    = "INTERNET"
}

# Ruta para root path
resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.graph_api.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.http_proxy.id}"
}

# Ruta para todos los demás paths
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