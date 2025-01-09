provider "aws" {
  region     = "us-east-1"
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
  token      = var.aws_session_token
}

# ... [resto de variables igual]

resource "aws_instance" "graph_ec2" {
  ami                         = "ami-0e731c8a588258d0d"
  instance_type               = "t2.micro"
  subnet_id                   = tolist(data.aws_subnets.default.ids)[0]
  vpc_security_group_ids      = [aws_security_group.graph_sg.id]
  key_name                    = aws_key_pair.deployer.key_name
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    set -e
    exec > >(tee /var/log/user-data.log) 2>&1

    # Actualizar e instalar dependencias
    dnf update -y
    dnf install -y python3-pip git nginx

    # Configurar permisos y directorio
    usermod -a -G wheel ec2-user
    chown -R ec2-user:ec2-user /home/ec2-user

    # Clonar repositorio
    cd /home/ec2-user
    git clone https://github.com/MeyDeiMey/grafo-mj.git app
    
    # Instalar dependencias de Python
    cd /home/ec2-user/app
    pip3 install -r requirements.txt
    pip3 install gunicorn flask-cors

    # Configurar Nginx
    cat > /etc/nginx/conf.d/graphword.conf << 'EOL'
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
    EOL

    # Eliminar la configuración default si existe
    rm -f /etc/nginx/conf.d/default.conf

    # Configurar y arrancar servicios
    systemctl enable nginx
    systemctl start nginx

    # Crear servicio systemd para la aplicación
    cat > /etc/systemd/system/graphapp.service << 'EOL'
    [Unit]
    Description=Graph Application Service
    After=network.target

    [Service]
    User=ec2-user
    WorkingDirectory=/home/ec2-user/app
    Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
    ExecStart=/usr/local/bin/gunicorn --bind 127.0.0.1:5001 api:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOL

    # Habilitar y arrancar el servicio
    systemctl daemon-reload
    systemctl enable graphapp
    systemctl start graphapp

    # Asegurar que los logs sean accesibles
    touch /home/ec2-user/app/app.log
    chown ec2-user:ec2-user /home/ec2-user/app/app.log
    chmod 644 /home/ec2-user/app/app.log
  EOF

  tags = {
    Name = "GraphWordInstance"
  }
}

resource "aws_apigatewayv2_api" "graph_api" {
  name          = "graph-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "http_proxy" {
  api_id           = aws_apigatewayv2_api.graph_api.id
  integration_type = "HTTP_PROXY"
  integration_uri  = "http://${aws_instance.graph_ec2.public_ip}:80"
  connection_type  = "INTERNET"
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
  value = aws_instance.graph_ec2.public_ip
}
# Test comment
