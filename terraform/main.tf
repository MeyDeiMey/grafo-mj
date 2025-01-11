# Provider configuration
provider "aws" {
  region = "us-east-1"
}

# Data source for default VPC
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security Group
resource "aws_security_group" "app_sg" {
  name_prefix = "graph-app-"
  description = "Security group for graph application"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic"
  }

  ingress {
    from_port   = 5001
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow application traffic"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "graph-app-sg"
  }
}

# EC2 Instance
resource "aws_instance" "app_server" {
  ami           = "ami-0e731c8a588258d0d"  # Amazon Linux 2023
  instance_type = "t2.micro"
  subnet_id     = tolist(data.aws_subnets.default.ids)[0]

  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    exec > >(tee /var/log/user-data.log) 2>&1

    # Update and install dependencies
    dnf update -y
    dnf install -y python3-pip git nginx

    # Configure permissions
    usermod -a -G wheel ec2-user
    chown -R ec2-user:ec2-user /home/ec2-user

    # Clone repository
    cd /home/ec2-user
    git clone https://github.com/MeyDeiMey/grafo-mj.git app
    
    # Install Python dependencies
    cd /home/ec2-user/app
    pip3 install -r requirements.txt
    pip3 install gunicorn flask-cors

    # Configure Nginx
    cat > /etc/nginx/conf.d/app.conf << 'EOL'
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

    rm -f /etc/nginx/conf.d/default.conf

    # Start Nginx
    systemctl enable nginx
    systemctl start nginx

    # Configure application service
    cat > /etc/systemd/system/graphapp.service << 'EOL'
    [Unit]
    Description=Graph Application Service
    After=network.target

    [Service]
    User=ec2-user
    WorkingDirectory=/home/ec2-user/app
    Environment="PATH=/home/ec2-user/.local/bin:/usr/local/bin:/usr/bin:/bin"
    ExecStart=/usr/local/bin/gunicorn --bind 127.0.0.1:5001 --workers 4 --timeout 120 api:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOL

    # Start application
    systemctl daemon-reload
    systemctl enable graphapp
    systemctl start graphapp
  EOF

  tags = {
    Name = "graph-app-server"
  }
}

# Outputs
output "app_url" {
  value = "http://${aws_instance.app_server.public_ip}"
}

output "instance_id" {
  value = aws_instance.app_server.id
}

output "public_ip" {
  value = aws_instance.app_server.public_ip
}